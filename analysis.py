from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def compare_lap_times(lap_a, lap_b):
    """Compare two laps using their recorded lap times."""
    time_a = lap_a["LapTime"].total_seconds()
    time_b = lap_b["LapTime"].total_seconds()

    if pd.isna(time_a) or pd.isna(time_b):
        raise ValueError("Both laps must have valid lap times.")

    return {
        "lap_a_seconds": time_a,
        "lap_b_seconds": time_b,
        "difference_seconds": time_b - time_a,
    }


def plot_speed_comparison(
    telemetry_a,
    telemetry_b,
    label_a="Lap A",
    label_b="Lap B",
    output_path="figures/lap_speed_comparison.png",
):
    """Plot speed against distance for two laps."""
    required = {"Distance", "Speed"}

    for label, telemetry in [
        (label_a, telemetry_a),
        (label_b, telemetry_b),
    ]:
        missing = required - set(telemetry.columns)
        if missing:
            raise ValueError(
                f"{label} is missing columns: {sorted(missing)}"
            )

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(telemetry_a["Distance"], telemetry_a["Speed"], label=label_a)
    ax.plot(telemetry_b["Distance"], telemetry_b["Speed"], label=label_b)

    ax.set(
        xlabel="Distance (m)",
        ylabel="Speed (km/h)",
        title="Lap Speed Comparison",
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")

    return fig, ax

def compare_sectors(lap_a, lap_b):
    """Compare sector times for two laps, in seconds."""
    sector_columns = [
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
    ]

    results = []

    for sector in sector_columns:
        time_a = lap_a.get(sector)
        time_b = lap_b.get(sector)

        valid_a = pd.notna(time_a)
        valid_b = pd.notna(time_b)

        seconds_a = time_a.total_seconds() if valid_a else float("nan")
        seconds_b = time_b.total_seconds() if valid_b else float("nan")

        difference = (
            seconds_b - seconds_a
            if valid_a and valid_b
            else float("nan")
        )

        results.append({
            "Sector": sector.replace("Time", ""),
            "Lap A (s)": seconds_a,
            "Lap B (s)": seconds_b,
            "Difference (s)": difference,
        })

    return pd.DataFrame(results)
