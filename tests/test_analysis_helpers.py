"""Unit tests for deterministic telemetry-analysis helpers in app.py."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path

import pandas as pd

# Stub Streamlit and TIF1 so tests can import the helper functions without
# starting the dashboard or making network calls.
streamlit_stub = types.ModuleType("streamlit")
streamlit_stub.cache_data = lambda **kwargs: (lambda fn: fn)
streamlit_stub.set_page_config = lambda *args, **kwargs: None
streamlit_stub.tabs = lambda *args, **kwargs: []
streamlit_stub.sidebar = types.SimpleNamespace()
sys.modules.setdefault("streamlit", streamlit_stub)
sys.modules.setdefault("tif1", types.ModuleType("tif1"))

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
SPEC = importlib.util.spec_from_file_location("f1_dashboard_under_test", APP_PATH)
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class LapDurationTests(unittest.TestCase):
    def test_duration_uses_time_span_in_seconds(self):
        df = pd.DataFrame({"Time": pd.to_timedelta(["0s", "1.25s", "2.5s"])})
        self.assertAlmostEqual(app.lap_duration_seconds(df), 2.5)

    def test_duration_returns_none_without_time_column(self):
        self.assertIsNone(app.lap_duration_seconds(pd.DataFrame({"Speed": [100, 120]})))

    def test_duration_returns_none_for_empty_data(self):
        self.assertIsNone(app.lap_duration_seconds(pd.DataFrame({"Time": pd.to_timedelta([])})))


class MetricValueTests(unittest.TestCase):
    def test_peak_speed(self):
        df = pd.DataFrame({"Speed": [100, 250, 180]})
        self.assertEqual(app.metric_value(df, "Speed"), 250.0)

    def test_mean_speed(self):
        df = pd.DataFrame({"Speed": [100, 200, 300]})
        self.assertEqual(app.metric_value(df, "Speed", "mean"), 200.0)

    def test_missing_column_returns_none(self):
        self.assertIsNone(app.metric_value(pd.DataFrame({"RPM": [9000]}), "Speed"))

    def test_empty_values_return_none(self):
        self.assertIsNone(app.metric_value(pd.DataFrame({"Speed": [None]}), "Speed"))


if __name__ == "__main__":
    unittest.main()
