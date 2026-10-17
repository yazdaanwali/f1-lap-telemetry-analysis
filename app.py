from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "data"
FIGURES = PROJECT / "figures"

st.set_page_config(
    page_title="F1 Telemetry Lab",
    page_icon="🏎️",
    layout="wide",
)

# /* F1_TELEMETRY_THEME */
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(ellipse at top right,
                rgba(170, 20, 35, 0.15), transparent 38%),
            #0b0d12;
        color: #f3f4f6;
    }

    [data-testid="stHeader"] {
        background: rgba(11, 13, 18, 0.85);
    }

    [data-testid="stSidebar"] {
        background: #11141b;
        border-right: 1px solid #292e39;
    }

    h1 {
        font-weight: 850 !important;
        letter-spacing: -1.2px;
    }

    h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #171b24, #11141b);
        border: 1px solid #303746;
        border-top: 3px solid #e10600;
        border-radius: 12px;
        padding: 18px 18px 14px 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #aeb6c5;
        font-size: 0.85rem;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: 800;
    }

    [data-testid="stTabs"] [role="tab"] {
        background: #151923;
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        border-bottom: 3px solid #e10600;
        color: #ffffff;
    }

    [data-testid="stPlotlyChart"] {
        background: #10131a;
        border: 1px solid #272d38;
        border-radius: 12px;
        padding: 8px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #303746;
        border-radius: 10px;
        overflow: hidden;
    }

    div.stDownloadButton > button {
        background: #e10600;
        color: white;
        border: 1px solid #e10600;
        border-radius: 8px;
        font-weight: 650;
    }

    div.stDownloadButton > button:hover {
        background: #b80500;
        color: white;
        border-color: #ff3028;
    }

    hr {
        border-color: #303746;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }
</style>
""", unsafe_allow_html=True)


st.title("🏎️ F1 Telemetry Lab")
st.caption(
    "2024 British Grand Prix • Qualifying • "
    "Historical telemetry analysis"
)

@st.cache_data
def load_telemetry(filename):
    path = DATA / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

lap_a = load_telemetry("lap_a_telemetry.csv")
lap_b = load_telemetry("lap_b_telemetry.csv")

sector_path = FIGURES / "sector_analysis.csv"
sectors = (
    pd.read_csv(sector_path)
    if sector_path.exists()
    else pd.DataFrame()
)

if lap_a.empty or lap_b.empty:
    st.error(
        "Telemetry CSV files are missing. "
        "Please save both lap telemetry files in the data folder."
    )
    st.stop()

for df in [lap_a, lap_b]:
    for column in [
        "Distance", "Speed", "Throttle", "RPM",
        "nGear", "X", "Y"
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

lap_a_name = "Lap 23"
lap_b_name = "Lap 20"

def metric_value(df, column, operation="max"):
    if column not in df.columns:
        return None
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if values.empty:
        return None
    if operation == "max":
        return float(values.max())
    if operation == "mean":
        return float(values.mean())
    return float(values.min())

# Overview metrics
m1, m2, m3, m4 = st.columns(4)

m1.metric("Lap A", "86.203 s", "Lap 23")
m2.metric("Lap B", "86.350 s", "Lap 20")
m3.metric("Lap time delta", "+0.147 s", "Lap B slower")
speed_a = metric_value(lap_a, "Speed")
speed_b = metric_value(lap_b, "Speed")
m4.metric(
    "Peak sampled speed",
    f"{max(speed_a or 0, speed_b or 0):.0f} km/h"
)

st.info(
    "Lap 23 and Lap 20 are separate qualifying laps. "
    "The distance traces are aligned by distance, not by elapsed time."
)

tabs = st.tabs([
    "Overview",
    "Telemetry",
    "Circuit map",
    "Sector analysis",
    "Time delta",
])

with tabs[0]:
    st.subheader("Speed vs distance")

    fig_speed = go.Figure()

    for df, name in [(lap_a, lap_a_name), (lap_b, lap_b_name)]:
        if {"Distance", "Speed"}.issubset(df.columns):
            clean = df.dropna(subset=["Distance", "Speed"]).sort_values("Distance")
            fig_speed.add_trace(go.Scatter(
                x=clean["Distance"],
                y=clean["Speed"],
                mode="lines",
                name=name,
                hovertemplate=(
                    "Distance: %{x:.0f} m<br>"
                    "Speed: %{y:.1f} km/h<extra>%{fullData.name}</extra>"
                ),
            ))

    fig_speed.update_layout(
        template="plotly_dark",
        xaxis_title="Distance along lap (m)",
        yaxis_title="Speed (km/h)",
        hovermode="x unified",
        legend_title="Comparison",
    )
    st.plotly_chart(fig_speed, use_container_width=True)

    st.subheader("Lap data summary")
    summary = pd.DataFrame({
        "Metric": [
            "Telemetry samples",
            "Maximum speed (km/h)",
            "Mean speed (km/h)",
            "Maximum RPM",
        ],
        lap_a_name: [
            len(lap_a),
            metric_value(lap_a, "Speed"),
            metric_value(lap_a, "Speed", "mean"),
            metric_value(lap_a, "RPM"),
        ],
        lap_b_name: [
            len(lap_b),
            metric_value(lap_b, "Speed"),
            metric_value(lap_b, "Speed", "mean"),
            metric_value(lap_b, "RPM"),
        ],
    })
    st.dataframe(summary.round(2), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Synchronized telemetry channels")

    available = [
        ("Speed", "Speed", "km/h"),
        ("Throttle", "Throttle", "%"),
        ("RPM", "RPM", "RPM"),
        ("Gear", "nGear", "gear"),
    ]

    has_brake = "Brake" in lap_a.columns and "Brake" in lap_b.columns

    row_titles = [item[0] for item in available]
    if has_brake:
        row_titles.insert(2, "Brake")

    fig = make_subplots(
        rows=len(row_titles),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.035,
        subplot_titles=row_titles,
    )

    for df, label in [(lap_a, lap_a_name), (lap_b, lap_b_name)]:
        df = df.sort_values("Distance")

        for row, (title, column, unit) in enumerate(available, start=1):
            if column not in df.columns or column == "Speed":
                # Speed is also included here as the first row.
                if column not in df.columns:
                    continue

            fig.add_trace(
                go.Scatter(
                    x=df["Distance"],
                    y=df[column],
                    mode="lines",
                    name=label,
                    legendgroup=label,
                    showlegend=(row == 1),
                    hovertemplate=(
                        "Distance: %{x:.0f} m<br>"
                        f"{title}: " + "%{y:.2f}<extra>" + label + "</extra>"
                    ),
                ),
                row=row,
                col=1,
            )

        if has_brake:
            brake_row = 3
            brake_values = df["Brake"].map(
                lambda value: 1 if str(value).lower() in ["true", "1"] else 0
            )
            fig.add_trace(
                go.Scatter(
                    x=df["Distance"],
                    y=brake_values,
                    mode="lines",
                    name=label,
                    legendgroup=label,
                    showlegend=False,
                    line_shape="hv",
                ),
                row=brake_row,
                col=1,
            )

    for row in range(1, len(row_titles) + 1):
        fig.update_yaxes(row=row, col=1, title_text=row_titles[row - 1])

    fig.update_xaxes(title_text="Distance (m)", row=len(row_titles), col=1)
    fig.update_layout(
        template="plotly_dark",
        height=900,
        hovermode="x",
        legend_title="Lap",
    )
    st.plotly_chart(fig, use_container_width=True)

    if "Throttle" in lap_a.columns and "Throttle" in lap_b.columns:
        st.caption(
            "Throttle values use the source's scale. "
            "Brake is displayed as 0 = off and 1 = on."
        )

with tabs[2]:
    st.subheader("Circuit position")

    required_xy = {"X", "Y"}
    if required_xy.issubset(lap_a.columns) and required_xy.issubset(lap_b.columns):
        track_fig = go.Figure()

        for df, label in [(lap_a, lap_a_name), (lap_b, lap_b_name)]:
            clean = df.dropna(subset=["X", "Y"]).sort_values("Distance")
            track_fig.add_trace(go.Scatter(
                x=clean["X"],
                y=clean["Y"],
                mode="lines",
                name=label,
                line=dict(width=3),
                customdata=clean[["Distance", "Speed"]].to_numpy()
                if "Speed" in clean.columns else None,
                hovertemplate=(
                    "X: %{x:.1f}<br>Y: %{y:.1f}<br>"
                    "Distance: %{customdata[0]:.0f} m<br>"
                    "Speed: %{customdata[1]:.1f} km/h<extra>%{fullData.name}</extra>"
                    if "Speed" in clean.columns
                    else "X: %{x:.1f}<br>Y: %{y:.1f}<extra>%{fullData.name}</extra>"
                ),
            ))

        track_fig.update_layout(
            template="plotly_dark",
            xaxis_title="X position",
            yaxis_title="Y position",
            yaxis_scaleanchor="x",
            yaxis_scaleratio=1,
            hovermode="closest",
        )
        st.plotly_chart(track_fig, use_container_width=True)
        st.caption(
            "This is a plot of the source's X/Y position coordinates, "
            "not a surveyed or geographically oriented circuit map."
        )
    else:
        st.warning("X/Y position columns are unavailable.")

with tabs[3]:
    st.subheader("Sector time comparison")

    if not sectors.empty and {
        "Sector", "Lap A (s)", "Lap B (s)", "Difference (s)"
    }.issubset(sectors.columns):
        sectors["Difference (s)"] = pd.to_numeric(
            sectors["Difference (s)"], errors="coerce"
        )

        fig_sector = px.bar(
            sectors,
            x="Sector",
            y="Difference (s)",
            color="Difference (s)",
            color_continuous_scale="RdYlGn_r",
            title="Lap B minus Lap A",
        )
        fig_sector.add_hline(y=0, line_dash="dash")
        fig_sector.update_layout(template="plotly_dark")
        st.plotly_chart(fig_sector, use_container_width=True)
        st.dataframe(sectors, use_container_width=True, hide_index=True)
    else:
        st.warning("Sector comparison CSV is missing or has unexpected columns.")


with tabs[4]:
    st.subheader("Elapsed-time delta by distance")
    st.caption(
        "Delta = Lap 20 elapsed time − Lap 23 elapsed time. "
        "Positive means Lap 20 is behind at that distance; "
        "negative means it is ahead."
    )

    import numpy as np

    def prepare_time_distance(df):
        clean = df[["Distance", "Time"]].copy()
        clean["Distance"] = pd.to_numeric(
            clean["Distance"], errors="coerce"
        )
        clean["ElapsedSeconds"] = (
            pd.to_timedelta(clean["Time"], errors="coerce")
            .dt.total_seconds()
        )
        clean = clean.dropna(
            subset=["Distance", "ElapsedSeconds"]
        )
        clean = clean.sort_values("Distance")
        clean = clean.drop_duplicates(
            subset=["Distance"], keep="first"
        )
        return clean

    a = prepare_time_distance(lap_a)
    b = prepare_time_distance(lap_b)

    if len(a) < 2 or len(b) < 2:
        st.warning("Not enough valid time-distance samples.")
    else:
        start_distance = max(a["Distance"].min(), b["Distance"].min())
        end_distance = min(a["Distance"].max(), b["Distance"].max())

        if end_distance <= start_distance:
            st.warning("The laps do not have a usable common distance range.")
        else:
            distance_grid = np.linspace(
                start_distance, end_distance, 600
            )

            time_a = np.interp(
                distance_grid, a["Distance"], a["ElapsedSeconds"]
            )
            time_b = np.interp(
                distance_grid, b["Distance"], b["ElapsedSeconds"]
            )
            delta = time_b - time_a

            delta_df = pd.DataFrame({
                "Distance (m)": distance_grid,
                "Time delta (s)": delta,
            })

            fig_delta = go.Figure()
            fig_delta.add_trace(go.Scatter(
                x=delta_df["Distance (m)"],
                y=delta_df["Time delta (s)"],
                mode="lines",
                name="Lap 20 − Lap 23",
                line=dict(width=2),
                fill="tozeroy",
                hovertemplate=(
                    "Distance: %{x:.0f} m<br>"
                    "Time delta: %{y:+.3f} s<extra></extra>"
                ),
            ))
            fig_delta.add_hline(
                y=0, line_dash="dash", line_color="white"
            )
            fig_delta.update_layout(
                template="plotly_dark",
                xaxis_title="Distance along lap (m)",
                yaxis_title="Elapsed-time delta (s)",
                hovermode="x unified",
            )
            st.plotly_chart(fig_delta, use_container_width=True)

            st.metric(
                "Delta at end of common distance",
                f"{delta[-1]:+.3f} s"
            )
            st.caption(
                "This is an interpolated telemetry estimate over the "
                "common distance range, not official sector timing. "
                "The laps occurred at different times and may have "
                "different conditions."
            )
            st.download_button(
                "Download time-delta data",
                data=delta_df.to_csv(index=False).encode("utf-8"),
                file_name="lap_time_delta.csv",
                mime="text/csv",
            )

report_path = PROJECT / "reports" / "lap_analysis_report.md"
if report_path.exists():
    with st.expander("View analysis report"):
        report_text = report_path.read_text(encoding="utf-8")
        st.markdown(report_text)
        st.download_button(
            "Download analysis report",
            data=report_text,
            file_name="lap_analysis_report.md",
            mime="text/markdown",
        )

st.divider()
st.caption(
    "Educational project using historical telemetry. "
    "This dashboard is not a live F1 timing system."
)
