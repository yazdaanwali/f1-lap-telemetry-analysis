"""Unit tests for deterministic telemetry-analysis helpers in app.py."""
import ast
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
wanted = {"lap_duration_seconds", "metric_value", "assess_lap_quality"}
helper_nodes = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted
]
if {node.name for node in helper_nodes} != wanted:
    raise RuntimeError("Expected telemetry helper functions were not found in app.py")

namespace = {"pd": pd, "np": np}
exec(compile(ast.Module(body=helper_nodes, type_ignores=[]), str(APP_PATH), "exec"), namespace)


class LapDurationTests(unittest.TestCase):
    def test_duration_uses_time_span_in_seconds(self):
        df = pd.DataFrame({"Time": pd.to_timedelta(["0s", "1.25s", "2.5s"])})
        self.assertAlmostEqual(namespace["lap_duration_seconds"](df), 2.5)

    def test_duration_returns_none_without_time_column(self):
        self.assertIsNone(
            namespace["lap_duration_seconds"](pd.DataFrame({"Speed": [100, 120]}))
        )

    def test_duration_ignores_invalid_timestamps(self):
        df = pd.DataFrame({"Time": ["bad", "1.5s", "2.0s"]})
        self.assertAlmostEqual(namespace["lap_duration_seconds"](df), 0.5)

    def test_duration_uses_span_when_timestamps_do_not_start_at_zero(self):
        df = pd.DataFrame({"Time": pd.to_timedelta(["2.0s", "40.0s", "92.5s"])})
        self.assertAlmostEqual(namespace["lap_duration_seconds"](df), 90.5)

    def test_duration_uses_min_and_max_even_if_rows_are_unsorted(self):
        df = pd.DataFrame({"Time": pd.to_timedelta(["5.0s", "2.0s", "3.5s"])})
        self.assertAlmostEqual(namespace["lap_duration_seconds"](df), 3.0)

    def test_duration_returns_none_for_empty_data(self):
        self.assertIsNone(
            namespace["lap_duration_seconds"](
                pd.DataFrame({"Time": pd.to_timedelta([])})
            )
        )


class MetricValueTests(unittest.TestCase):
    def test_peak_speed(self):
        df = pd.DataFrame({"Speed": [100, 250, 180]})
        self.assertEqual(namespace["metric_value"](df, "Speed"), 250.0)

    def test_mean_speed(self):
        df = pd.DataFrame({"Speed": [100, 200, 300]})
        self.assertEqual(namespace["metric_value"](df, "Speed", "mean"), 200.0)

    def test_non_numeric_speed_values_are_ignored(self):
        df = pd.DataFrame({"Speed": ["slow", "220", None, "180"]})
        self.assertEqual(namespace["metric_value"](df, "Speed"), 220.0)

    def test_minimum_speed(self):
        df = pd.DataFrame({"Speed": [100, 250, 180]})
        self.assertEqual(namespace["metric_value"](df, "Speed", "min"), 100.0)

    def test_missing_column_returns_none(self):
        self.assertIsNone(
            namespace["metric_value"](pd.DataFrame({"RPM": [9000]}), "Speed")
        )

    def test_empty_values_return_none(self):
        self.assertIsNone(
            namespace["metric_value"](pd.DataFrame({"Speed": [None]}), "Speed")
        )


class TelemetryQualityTests(unittest.TestCase):
    def assess(self, frame):
        return namespace["assess_lap_quality"](
            frame,
            {"Sector1Time": 1.0, "Sector2Time": 1.0, "Sector3Time": 1.0},
            "Test lap",
        )

    def test_flags_repeated_distance_samples(self):
        frame = pd.DataFrame({
            "Distance": [0, 0, 1200],
            "Speed": [0, 50, 100],
            "Time": pd.to_timedelta(["0s", "1s", "2s"]),
        })
        issues = self.assess(frame)
        self.assertTrue(any("repeated distance" in issue for issue in issues))

    def test_flags_distance_moving_backwards(self):
        frame = pd.DataFrame({
            "Distance": [0, 1200, 1100],
            "Speed": [0, 100, 90],
            "Time": pd.to_timedelta(["0s", "1s", "2s"]),
        })
        issues = self.assess(frame)
        self.assertTrue(any("distance decreases" in issue for issue in issues))

    def test_flags_invalid_values_and_implausible_speed(self):
        frame = pd.DataFrame({
            "Distance": [0, 1200, None],
            "Speed": [0, 450, "invalid"],
            "Time": pd.to_timedelta(["0s", "1s", "2s"]),
        })
        issues = self.assess(frame)
        self.assertTrue(any("missing or invalid distance" in issue for issue in issues))
        self.assertTrue(any("exceed 400 km/h" in issue for issue in issues))
        self.assertTrue(any("missing or invalid speed" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
