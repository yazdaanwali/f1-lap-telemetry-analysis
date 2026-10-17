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
st.caption("User-selected historical session • Interactive telemetry analysis")

# User selection controls and dynamic telemetry retrieval
st.subheader("Choose a session to analyse")
st.caption("Choose a historical session, driver and two laps to compare.")

control_col1, control_col2, control_col3 = st.columns(3)
with control_col1:
    selected_season = st.selectbox("Season", [2023, 2024, 2025], index=1, key="selected_season")
    selected_grand_prix = st.selectbox(
        "Grand Prix",
        ["Bahrain Grand Prix", "British Grand Prix", "Italian Grand Prix", "Monaco Grand Prix"],
        index=1,
        key="selected_grand_prix",
    )
with control_col2:
    selected_session = st.selectbox(
        "Session", ["Practice", "Qualifying", "Race"], index=2, key="selected_session"
    )
    driver_options = {
        "HAM — Lewis Hamilton": "HAM",
        "VER — Max Verstappen": "VER",
        "LEC — Charles Leclerc": "LEC",
        "NOR — Lando Norris": "NOR",
    }
    selected_driver = st.selectbox(
        "Driver", list(driver_options.keys()), index=0, key="selected_driver"
    )
with control_col3:
    selected_lap_a = st.number_input(
        "Lap A", min_value=1, max_value=80, value=1, step=1, key="selected_lap_a"
    )
    selected_lap_b = st.number_input(
        "Lap B", min_value=1, max_value=80, value=23, step=1, key="selected_lap_b"
    )

@st.cache_data(show_spinner=False)
def fetch_lap_telemetry(season, grand_prix, session_name, driver_code, lap_number):
    import tif1

    session_data = tif1.get_session(season, grand_prix, session_name)
    driver_data = session_data.get_driver(driver_code)
    lap_data = driver_data.get_lap(int(lap_number))
    # TIF1's Telemetry wrapper contains a Session object and thread locks,
    # which Streamlit cannot pickle. Return only a plain pandas DataFrame.
    telemetry_data = pd.DataFrame(lap_data.telemetry).copy()

    required = {"Distance", "Speed", "Throttle", "RPM", "nGear", "X", "Y", "Time"}
    missing = required.difference(telemetry_data.columns)
    if missing:
        raise ValueError(f"Telemetry is missing required columns: {sorted(missing)}")
    return telemetry_data

selection = (
    int(selected_season), selected_grand_prix, selected_session,
    driver_options[selected_driver], int(selected_lap_a), int(selected_lap_b)
)
st.caption(
    f"Selected: {selection[0]} · {selection[1]} · {selection[2]} · "
    f"{selected_driver} · Laps {selection[4]} and {selection[5]}"
)

if selection[4] == selection[5]:
    st.warning("Choose two different lap numbers to compare.")
    st.stop()

try:
    with st.spinner("Retrieving session and telemetry data…"):
        lap_a = fetch_lap_telemetry(*selection[:4], selection[4])
        lap_b = fetch_lap_telemetry(*selection[:4], selection[5])
except Exception as exc:
    st.error(
        "Could not load the selected telemetry. Check that the session, driver and "
        "lap numbers are available, then try again. The data provider may also be "
        "temporarily unavailable."
    )
    st.exception(exc)
    st.stop()

for df in [lap_a, lap_b]:
    for column in ["Distance", "Speed", "Throttle", "RPM", "nGear", "X", "Y"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

lap_a_name = f"Lap {selection[4]}"
lap_b_name = f"Lap {selection[5]}"

@st.cache_data(show_spinner=False)
def fetch_sector_times(season, grand_prix, session_name, driver_code, lap_number):
    """Return serializable official sector timing values for one selected lap."""
    import tif1

    session_data = tif1.get_session(season, grand_prix, session_name)
    driver_data = session_data.get_driver(driver_code)
    laps_table = pd.DataFrame(driver_data.laps).copy()

    if "LapNumber" not in laps_table.columns:
        return {"LapNumber": int(lap_number), "Sector1Time": None,
                "Sector2Time": None, "Sector3Time": None}

    lap_rows = laps_table[
        pd.to_numeric(laps_table["LapNumber"], errors="coerce") == int(lap_number)
    ]
    if lap_rows.empty:
        raise ValueError(f"Lap {lap_number} was not found in the timing table.")

    row = lap_rows.iloc[0]
    result = {"LapNumber": int(lap_number)}
    for col in ["Sector1Time", "Sector2Time", "Sector3Time"]:
        value = row.get(col)
        if pd.isna(value):
            result[col] = None
        else:
            try:
                result[col] = float(pd.to_timedelta(value).total_seconds())
            except (TypeError, ValueError):
                try:
                    result[col] = float(value)
                except (TypeError, ValueError):
                    result[col] = None
    return result

try:
    sector_a = fetch_sector_times(*selection[:4], selection[4])
    sector_b = fetch_sector_times(*selection[:4], selection[5])
    sector_rows = []
    for idx, col in enumerate(["Sector1Time", "Sector2Time", "Sector3Time"], start=1):
        value_a = sector_a.get(col)
        value_b = sector_b.get(col)
        sector_rows.append({
            "Sector": f"Sector {idx}",
            "Lap A (s)": value_a,
            "Lap B (s)": value_b,
            "Difference (s)": (
                value_b - value_a
                if value_a is not None and value_b is not None else np.nan
            ),
        })
    sectors = pd.DataFrame(sector_rows)
except Exception as exc:
    sectors = pd.DataFrame()
    sector_error = str(exc)
else:
    sector_error = None

# Data-quality checks for sector comparisons. These flags prompt verification;
# they do not automatically classify a lap as invalid.
sector_quality_issues = []
if not sectors.empty:
    for _, row in sectors.iterrows():
        sector_name = row["Sector"]
        time_a = row["Lap A (s)"]
        time_b = row["Lap B (s)"]
        difference = row["Difference (s)"]
        if pd.isna(time_a) or pd.isna(time_b):
            missing_laps = []
            if pd.isna(time_a):
                missing_laps.append(lap_a_name)
            if pd.isna(time_b):
                missing_laps.append(lap_b_name)
            sector_quality_issues.append(
                f"{sector_name}: timing is missing for {' and '.join(missing_laps)}."
            )
        elif pd.notna(difference) and abs(float(difference)) >= 3.0:
            sector_quality_issues.append(
                f"{sector_name}: the sector difference is {float(difference):+.3f} s, "
                "which is unusually large and should be checked against the lap context."
            )

# Telemetry-based lap quality checks. These are screening indicators, not
# official classifications; they cannot prove a lap was a clean flying lap.
def assess_lap_quality(df, sector_record, lap_label):
    issues = []
    required = ["Distance", "Speed", "Time"]
    missing_columns = [column for column in required if column not in df.columns]
    if missing_columns:
        issues.append(f"{lap_label}: missing telemetry columns: {', '.join(missing_columns)}.")
        return issues

    clean = df.copy()
    clean["Distance"] = pd.to_numeric(clean["Distance"], errors="coerce")
    clean["Speed"] = pd.to_numeric(clean["Speed"], errors="coerce")
    clean["ElapsedSeconds"] = pd.to_timedelta(clean["Time"], errors="coerce").dt.total_seconds()
    usable = clean.dropna(subset=["Distance", "Speed", "ElapsedSeconds"])

    if len(usable) < 100:
        issues.append(
            f"{lap_label}: only {len(usable)} usable telemetry samples; "
            "the lap may be incomplete or the data may be sparse."
        )
    if usable.empty:
        issues.append(f"{lap_label}: no usable distance, speed and time samples.")
    else:
        distance_span = float(usable["Distance"].max() - usable["Distance"].min())
        if distance_span < 1000:
            issues.append(
                f"{lap_label}: telemetry covers only {distance_span:.0f} m; "
                "this does not look like a full circuit lap."
            )
        if (usable["Speed"] < 0).any():
            issues.append(f"{lap_label}: negative speed values were found; inspect the source data.")
        time_steps = usable["ElapsedSeconds"].diff().dropna()
        if (time_steps < 0).any():
            issues.append(f"{lap_label}: telemetry timestamps are not monotonic.")
    missing_sector_times = [
        name for name in ["Sector1Time", "Sector2Time", "Sector3Time"]
        if sector_record.get(name) is None or pd.isna(sector_record.get(name))
    ]
    if missing_sector_times:
        sector_names = ", ".join(name.replace("Time", "").replace("Sector", "Sector ") for name in missing_sector_times)
        issues.append(f"{lap_label}: official timing is missing {sector_names}.")
    return issues

lap_quality_issues = []
if not sectors.empty:
    lap_quality_issues.extend(assess_lap_quality(lap_a, sector_a, lap_a_name))
    lap_quality_issues.extend(assess_lap_quality(lap_b, sector_b, lap_b_name))

def lap_duration_seconds(df):
    if "Time" not in df.columns:
        return None
    values = pd.to_timedelta(df["Time"], errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.max().total_seconds())

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

m1.metric("Lap A telemetry duration", f"{lap_duration_seconds(lap_a):.3f} s" if lap_duration_seconds(lap_a) is not None else "Unavailable", lap_a_name)
m2.metric("Lap B telemetry duration", f"{lap_duration_seconds(lap_b):.3f} s" if lap_duration_seconds(lap_b) is not None else "Unavailable", lap_b_name)
m3.metric("Telemetry duration delta", f"{lap_duration_seconds(lap_b) - lap_duration_seconds(lap_a):+.3f} s" if lap_duration_seconds(lap_a) is not None and lap_duration_seconds(lap_b) is not None else "Unavailable", "B minus A")
speed_a = metric_value(lap_a, "Speed")
speed_b = metric_value(lap_b, "Speed")
m4.metric(
    "Peak sampled speed",
    f"{max(speed_a or 0, speed_b or 0):.0f} km/h"
)

st.info(
    "Telemetry is loaded for the selected driver and laps. Duration values above are derived from telemetry timestamps, not official timing classifications."
)

def lap_classification(df, sector_record, lap_label):
    issues = assess_lap_quality(df, sector_record, lap_label)
    if issues:
        return "Needs review", issues
    return "Complete data", []

lap_a_status, lap_a_issues = lap_classification(lap_a, sector_a, lap_a_name)
lap_b_status, lap_b_issues = lap_classification(lap_b, sector_b, lap_b_name)
pair_status = (
    "Needs review"
    if lap_a_status == "Needs review" or lap_b_status == "Needs review"
    else "Comparability uncertain"
)

with st.expander("Lap validation and classification", expanded=bool(lap_quality_issues)):
    st.caption(
        "These are automated data-screening labels, not official FIA lap classifications. "
        "Complete data means basic checks passed; it does not prove a clean flying lap."
    )
    status_col_a, status_col_b, status_col_pair = st.columns(3)
    with status_col_a:
        st.metric(f"{lap_a_name} classification", lap_a_status)
    with status_col_b:
        st.metric(f"{lap_b_name} classification", lap_b_status)
    with status_col_pair:
        st.metric("Comparison classification", pair_status)

    if lap_quality_issues:
        st.warning("Review these data-quality notes before interpreting the comparison.")
        for issue in lap_quality_issues:
            st.write(f"• {issue}")
    else:
        st.success(
            "Both laps passed the basic telemetry and sector-availability checks. "
            "The comparison remains uncertain because lap type, traffic, tyres, weather "
            "and other conditions are not verified by these checks."
        )

tabs = st.tabs([
    "Overview",
    "Telemetry",
    "Circuit map",
    "Sector analysis",
    "Time delta",
    "Braking & corners",
    "Corner comparison",
    "Driver scorecard",
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

    st.subheader("Automatic engineering insights")
    st.caption(
        "These observations are calculated from the selected telemetry samples. "
        "They are not official lap classifications or proof of a driving cause."
    )

    speed_gap = metric_value(lap_b, "Speed") - metric_value(lap_a, "Speed")
    mean_speed_gap = metric_value(lap_b, "Speed", "mean") - metric_value(lap_a, "Speed", "mean")

    def sample_share(df, column, predicate):
        if column not in df.columns or df.empty:
            return None
        values = df[column]
        try:
            selected = predicate(values)
            return float(selected.fillna(False).mean() * 100)
        except (TypeError, ValueError):
            return None

    full_throttle_a = sample_share(lap_a, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95)
    full_throttle_b = sample_share(lap_b, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95)
    braking_a = sample_share(
        lap_a, "Brake",
        lambda x: x.astype(str).str.strip().str.lower().isin(["true", "1", "1.0"])
    )
    braking_b = sample_share(
        lap_b, "Brake",
        lambda x: x.astype(str).str.strip().str.lower().isin(["true", "1", "1.0"])
    )

    insight_col1, insight_col2 = st.columns(2)
    with insight_col1:
        if speed_gap is not None:
            leader = "Lap B" if speed_gap > 0 else "Lap A" if speed_gap < 0 else "Both laps"
            st.markdown(
                f"**Peak speed:** {leader} has the higher sampled peak by "
                f"{abs(speed_gap):.1f} km/h."
            )
        if mean_speed_gap is not None:
            leader = "Lap B" if mean_speed_gap > 0 else "Lap A" if mean_speed_gap < 0 else "Both laps"
            st.markdown(
                f"**Mean sampled speed:** {leader} is higher by "
                f"{abs(mean_speed_gap):.1f} km/h."
            )
    with insight_col2:
        if full_throttle_a is not None and full_throttle_b is not None:
            st.markdown(
                f"**High-throttle samples (≥95%):** {lap_a_name} "
                f"{full_throttle_a:.1f}% · {lap_b_name} {full_throttle_b:.1f}%."
            )
        if braking_a is not None and braking_b is not None:
            st.markdown(
                f"**Brake-on samples:** {lap_a_name} {braking_a:.1f}% · "
                f"{lap_b_name} {braking_b:.1f}%."
            )
    st.info(
        "Interpret these indicators in context: telemetry sampling, track conditions, "
        "traffic, tyre state and whether a lap is a formation/out-lap can affect the comparison."
    )

with tabs[1]:
    st.subheader("Synchronized telemetry channels")

    has_brake = "Brake" in lap_a.columns and "Brake" in lap_b.columns

    channels = [
        ("Speed", "Speed"),
        ("Throttle", "Throttle"),
    ]
    if has_brake:
        channels.append(("Brake", "Brake"))
    channels.extend([
        ("RPM", "RPM"),
        ("Gear", "nGear"),
    ])

    # Align both laps to the same distance grid so values are compared at
    # matching approximate positions, despite different telemetry sample spacing.
    def prepare_overlay_data(df):
        data = df.copy()
        data["Distance"] = pd.to_numeric(data["Distance"], errors="coerce")
        for _, column in channels:
            if column != "Brake" and column in data.columns:
                data[column] = pd.to_numeric(data[column], errors="coerce")
        if "Brake" in data.columns:
            data["Brake"] = data["Brake"].astype(str).str.strip().str.lower().isin(
                ["true", "1", "1.0"]
            ).astype(float)
        data = (
            data.dropna(subset=["Distance"])
            .sort_values("Distance")
            .drop_duplicates(subset=["Distance"], keep="first")
        )
        return data

    overlay_a = prepare_overlay_data(lap_a)
    overlay_b = prepare_overlay_data(lap_b)
    common_start = max(overlay_a["Distance"].min(), overlay_b["Distance"].min())
    common_end = min(overlay_a["Distance"].max(), overlay_b["Distance"].max())

    if common_end <= common_start:
        st.warning("These laps do not have a usable shared distance range for aligned overlay.")
    else:
        grid_size = min(1500, max(300, min(len(overlay_a), len(overlay_b))))
        distance_grid = np.linspace(common_start, common_end, grid_size)

        def values_on_grid(data, column):
            if column not in data.columns:
                return None
            clean = data[["Distance", column]].dropna()
            if len(clean) < 2:
                return None
            values = np.interp(
                distance_grid,
                clean["Distance"].to_numpy(dtype=float),
                clean[column].to_numpy(dtype=float),
            )
            if column == "Brake":
                values = (values >= 0.5).astype(int)
            return values

        fig = make_subplots(
            rows=len(channels),
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.035,
            subplot_titles=[name for name, _ in channels],
        )

        for label, data in [(lap_a_name, overlay_a), (lap_b_name, overlay_b)]:
            for row, (title, column) in enumerate(channels, start=1):
                values = values_on_grid(data, column)
                if values is None:
                    continue
                is_brake = column == "Brake"
                fig.add_trace(
                    go.Scatter(
                        x=distance_grid,
                        y=values,
                        mode="lines",
                        name=label,
                        legendgroup=label,
                        showlegend=(row == 1),
                        line_shape="hv" if is_brake else "linear",
                        hovertemplate=(
                            "Aligned distance: %{x:.0f} m<br>"
                            f"{title}: " + "%{y:.2f}<extra>" + label + "</extra>"
                        ),
                    ),
                    row=row,
                    col=1,
                )

    for row, (title, column) in enumerate(channels, start=1):
        fig.update_yaxes(row=row, col=1, title_text=title)

    fig.update_xaxes(title_text="Distance (m)", row=len(channels), col=1)
    fig.update_layout(
        template="plotly_dark",
        height=900,
        hovermode="x",
        legend_title="Lap",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Both laps are interpolated onto a shared distance grid over their overlapping distance range. "
        "Continuous channels are linearly interpolated; brake is thresholded back to 0 = off and 1 = on. "
        "This aligns distance, not elapsed time, and does not remove differences caused by conditions or lap type."
    )

with tabs[2]:
    st.subheader("Circuit position")
    st.caption(
        "Track coordinates with detected brake-on samples and candidate low-speed points. "
        "Markers are telemetry-derived estimates, not official corner numbers."
    )

    required_xy = {"X", "Y"}
    if required_xy.issubset(lap_a.columns) and required_xy.issubset(lap_b.columns):
        track_fig = go.Figure()

        for df, label in [(lap_a, lap_a_name), (lap_b, lap_b_name)]:
            clean = df.dropna(subset=["X", "Y"]).sort_values("Distance")
            customdata = clean[["Distance", "Speed"]].to_numpy() if "Speed" in clean.columns else None
            track_fig.add_trace(go.Scatter(
                x=clean["X"], y=clean["Y"], mode="lines", name=label,
                line=dict(width=3), customdata=customdata,
                hovertemplate=(
                    "X: %{x:.1f}<br>Y: %{y:.1f}<br>"
                    "Distance: %{customdata[0]:.0f} m<br>"
                    "Speed: %{customdata[1]:.1f} km/h<extra>%{fullData.name}</extra>"
                    if "Speed" in clean.columns
                    else "X: %{x:.1f}<br>Y: %{y:.1f}<extra>%{fullData.name}</extra>"
                ),
            ))

        # Overlay brake-on samples as markers on each lap's own track trace.
        for df, label, symbol in [
            (lap_a, f"{lap_a_name} braking", "circle"),
            (lap_b, f"{lap_b_name} braking", "x"),
        ]:
            if "Brake" in df.columns:
                points = df[
                    df["Brake"].astype(str).str.strip().str.lower().isin(["true", "1", "1.0"])
                ].dropna(subset=["X", "Y"])
                track_fig.add_trace(go.Scatter(
                    x=points["X"], y=points["Y"], mode="markers", name=label,
                    marker=dict(size=6, symbol=symbol),
                    customdata=points[["Distance", "Speed"]].to_numpy()
                    if {"Distance", "Speed"}.issubset(points.columns) else None,
                    hovertemplate=(
                        "Brake active<br>X: %{x:.1f}<br>Y: %{y:.1f}<br>"
                        "Distance: %{customdata[0]:.0f} m<br>"
                        "Speed: %{customdata[1]:.1f} km/h<extra>%{fullData.name}</extra>"
                        if {"Distance", "Speed"}.issubset(points.columns)
                        else "Brake active<br>X: %{x:.1f}<br>Y: %{y:.1f}<extra>%{fullData.name}</extra>"
                    ),
                ))

        # Overlay local low-speed minima; spacing prevents dense marker clusters.
        for df, label, symbol in [
            (lap_a, f"{lap_a_name} low-speed points", "diamond"),
            (lap_b, f"{lap_b_name} low-speed points", "square"),
        ]:
            required = {"X", "Y", "Distance", "Speed"}
            if required.issubset(df.columns):
                points = df.dropna(subset=["X", "Y", "Distance", "Speed"]).sort_values("Distance").reset_index(drop=True)
                speeds = pd.to_numeric(points["Speed"], errors="coerce").to_numpy()
                distances = pd.to_numeric(points["Distance"], errors="coerce").to_numpy()
                minima = [
                    i for i in range(1, len(points) - 1)
                    if np.isfinite(speeds[i-1:i+2]).all()
                    and speeds[i] <= speeds[i-1] and speeds[i] < speeds[i+1]
                ]
                minima.sort(key=lambda i: speeds[i])
                chosen = []
                for i in minima:
                    if all(abs(distances[i] - distances[j]) >= 120 for j in chosen):
                        chosen.append(i)
                points = points.iloc[sorted(chosen)].copy()
                track_fig.add_trace(go.Scatter(
                    x=points["X"], y=points["Y"], mode="markers", name=label,
                    marker=dict(size=9, symbol=symbol),
                    customdata=points[["Distance", "Speed"]].to_numpy(),
                    hovertemplate=(
                        "Candidate low-speed point<br>Distance: %{customdata[0]:.0f} m<br>"
                        "Speed: %{customdata[1]:.1f} km/h<extra>%{fullData.name}</extra>"
                    ),
                ))

        track_fig.update_layout(
            template="plotly_dark", xaxis_title="X position", yaxis_title="Y position",
            yaxis_scaleanchor="x", yaxis_scaleratio=1, hovermode="closest",
            legend_title="Telemetry layer",
        )
        st.plotly_chart(track_fig, use_container_width=True)
        st.caption(
            "This uses the source's X/Y coordinates, not surveyed geographic coordinates. "
            "Brake markers can overlap and dense braking traces may be simplified visually."
        )
    else:
        st.warning("X/Y position columns are unavailable.")

    required_xy = {"X", "Y"}
    if required_xy.issubset(lap_a.columns) and required_xy.issubset(lap_b.columns):
        track_fig = go.Figure()
        for df, label in [(lap_a, lap_a_name), (lap_b, lap_b_name)]:
            clean = df.dropna(subset=["X", "Y"]).sort_values("Distance")
            customdata = clean[["Distance", "Speed"]].to_numpy() if "Speed" in clean.columns else None
            track_fig.add_trace(go.Scatter(
                x=clean["X"], y=clean["Y"], mode="lines", name=label,
                line=dict(width=3), customdata=customdata,
                hovertemplate=(
                    "X: %{x:.1f}<br>Y: %{y:.1f}<br>"
                    "Distance: %{customdata[0]:.0f} m<br>"
                    "Speed: %{customdata[1]:.1f} km/h<extra>%{fullData.name}</extra>"
                    if "Speed" in clean.columns
                    else "X: %{x:.1f}<br>Y: %{y:.1f}<extra>%{fullData.name}</extra>"
                ),
            ))
        track_fig.update_layout(
            template="plotly_dark", xaxis_title="X position", yaxis_title="Y position",
            yaxis_scaleanchor="x", yaxis_scaleratio=1, hovermode="closest",
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
    st.caption(
        f"Official sector timing for {selected_driver}, {selected_grand_prix}, "
        f"{selected_session}. Difference = {lap_b_name} − {lap_a_name}; "
        "negative means Lap B was faster in that sector."
    )
    if sector_quality_issues:
        st.warning(
            "Data-quality check: review the notes below before interpreting these "
            "sector differences as a performance comparison."
        )
        for issue in sector_quality_issues:
            st.write(f"• {issue}")
    else:
        st.success("Sector timing check: all three sector times are present and no unusually large sector difference was flagged.")
    if not sectors.empty and sectors[["Lap A (s)", "Lap B (s)"]].notna().any().any():
        chart_sectors = sectors.dropna(subset=["Difference (s)"])
        if not chart_sectors.empty:
            fig_sector = px.bar(
                chart_sectors, x="Sector", y="Difference (s)",
                color="Difference (s)", color_continuous_scale="RdYlGn_r",
                title=f"Sector time difference ({lap_b_name} minus {lap_a_name})",
            )
            fig_sector.add_hline(y=0, line_dash="dash")
            fig_sector.update_layout(template="plotly_dark", yaxis_title="Time difference (seconds)")
            st.plotly_chart(fig_sector, use_container_width=True)
        st.dataframe(sectors.round(3), use_container_width=True, hide_index=True)
        for _, row in sectors.dropna(subset=["Difference (s)"]).iterrows():
            diff = row["Difference (s)"]
            outcome = "faster" if diff < 0 else "slower" if diff > 0 else "equal"
            st.write(f"**{row['Sector']}:** Lap B was {abs(diff):.3f} s {outcome} than Lap A.")
        st.download_button(
            "Download sector comparison CSV",
            data=sectors.to_csv(index=False).encode("utf-8"),
            file_name="selected_lap_sector_comparison.csv", mime="text/csv",
        )
    else:
        st.warning(
            "Official sector timing is unavailable for one or both selected laps. "
            "No sector comparison is shown rather than estimating sector times from telemetry."
        )
        if sector_error:
            st.caption(f"Data-source detail: {sector_error}")

with tabs[4]:
    st.subheader("Elapsed-time delta by distance")
    st.caption(
        f"Delta = {lap_b_name} elapsed time − {lap_a_name} elapsed time. "
        "Positive means Lap B is behind at that distance; negative means it is ahead."
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
                name=f"{lap_b_name} − {lap_a_name}",
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

with tabs[5]:
    st.subheader("Braking and corner analysis")
    st.caption(
        "Compare sampled braking events, speed minima and throttle application by distance. "
        "This is a telemetry-based heuristic, not a certified corner segmentation."
    )

    def prepare_braking_data(df):
        needed = {"Distance", "Speed", "Throttle", "Brake"}
        if not needed.issubset(df.columns):
            return pd.DataFrame()
        out = df[["Distance", "Speed", "Throttle", "Brake"]].copy()
        out["Distance"] = pd.to_numeric(out["Distance"], errors="coerce")
        out["Speed"] = pd.to_numeric(out["Speed"], errors="coerce")
        out["Throttle"] = pd.to_numeric(out["Throttle"], errors="coerce")
        out["BrakeOn"] = out["Brake"].astype(str).str.strip().str.lower().isin(
            ["true", "1", "1.0"]
        )
        return out.dropna(subset=["Distance", "Speed", "Throttle"]).sort_values("Distance")

    brake_a = prepare_braking_data(lap_a)
    brake_b = prepare_braking_data(lap_b)

    if brake_a.empty or brake_b.empty:
        st.warning(
            "Braking analysis needs Distance, Speed, Throttle and Brake signals "
            "for both selected laps. One or more signals are unavailable."
        )
    else:
        def detect_braking_events(data, lap_label):
            data = data.reset_index(drop=True).copy()
            data["BrakeGroup"] = data["BrakeOn"].ne(data["BrakeOn"].shift()).cumsum()
            events = []
            for _, group in data[data["BrakeOn"]].groupby("BrakeGroup"):
                if len(group) < 2:
                    continue
                start = group.iloc[0]
                end = group.iloc[-1]
                events.append({
                    "Lap": lap_label,
                    "Start distance (m)": float(start["Distance"]),
                    "End distance (m)": float(end["Distance"]),
                    "Approx. event length (m)": float(end["Distance"] - start["Distance"]),
                    "Entry speed (km/h)": float(start["Speed"]),
                    "Minimum speed during brake event (km/h)": float(group["Speed"].min()),
                    "Throttle at event end (%)": float(end["Throttle"]),
                })
            return events

        events = detect_braking_events(brake_a, lap_a_name) + detect_braking_events(brake_b, lap_b_name)
        if not events:
            st.info("No multi-sample braking events were detected in these laps.")
        else:
            event_df = pd.DataFrame(events)
            st.markdown("**Detected braking events**")
            st.dataframe(event_df.round(1), use_container_width=True, hide_index=True)

            event_fig = go.Figure()
            for data, label in [(brake_a, lap_a_name), (brake_b, lap_b_name)]:
                event_fig.add_trace(go.Scatter(
                    x=data["Distance"], y=data["Speed"], mode="lines",
                    name=f"{label} speed",
                    hovertemplate="Distance: %{x:.0f} m<br>Speed: %{y:.1f} km/h<extra>%{fullData.name}</extra>",
                ))
                brake_points = data[data["BrakeOn"]]
                event_fig.add_trace(go.Scatter(
                    x=brake_points["Distance"], y=brake_points["Speed"],
                    mode="markers", name=f"{label} brake on",
                    marker=dict(size=5, symbol="circle"),
                    hovertemplate="Brake active<br>Distance: %{x:.0f} m<br>Speed: %{y:.1f} km/h<extra>%{fullData.name}</extra>",
                ))
            event_fig.update_layout(
                template="plotly_dark", xaxis_title="Distance along lap (m)",
                yaxis_title="Speed (km/h)", hovermode="x unified",
            )
            st.plotly_chart(event_fig, use_container_width=True)
            st.download_button(
                "Download braking-event CSV",
                data=event_df.to_csv(index=False).encode("utf-8"),
                file_name="braking_event_comparison.csv", mime="text/csv",
            )

        st.markdown("**Low-speed points (possible corner-apex indicators)**")
        corner_rows = []
        for data, label in [(brake_a, lap_a_name), (brake_b, lap_b_name)]:
            speed = data["Speed"].to_numpy()
            distance = data["Distance"].to_numpy()
            if len(data) < 3:
                continue
            candidates = [
                i for i in range(1, len(speed) - 1)
                if speed[i] <= speed[i - 1] and speed[i] < speed[i + 1]
            ]
            candidates.sort(key=lambda i: speed[i])
            kept = []
            for i in candidates:
                if all(abs(distance[i] - distance[j]) >= 100 for j in kept):
                    kept.append(i)
            for i in sorted(kept, key=lambda j: distance[j]):
                corner_rows.append({
                    "Lap": label,
                    "Distance (m)": float(distance[i]),
                    "Local minimum speed (km/h)": float(speed[i]),
                    "Throttle at point (%)": float(data.iloc[i]["Throttle"]),
                    "Brake active": bool(data.iloc[i]["BrakeOn"]),
                })
        if corner_rows:
            corners_df = pd.DataFrame(corner_rows)
            st.dataframe(corners_df.round(1), use_container_width=True, hide_index=True)
            st.download_button(
                "Download low-speed points CSV",
                data=corners_df.to_csv(index=False).encode("utf-8"),
                file_name="low_speed_corner_indicators.csv", mime="text/csv",
            )
        else:
            st.info("Not enough telemetry samples to identify local low-speed points.")

with tabs[6]:
    st.subheader("Corner-by-corner comparison")
    st.caption(
        "Candidate corners are estimated from local speed minima and matched by distance. "
        "These are exploratory indicators, not official corner labels."
    )

    def corner_candidates(df, label):
        required = ["Distance", "Speed", "Throttle"]
        if not set(required).issubset(df.columns):
            return pd.DataFrame()
        data = df[required].copy()
        for col in required:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        data = data.dropna().sort_values("Distance").drop_duplicates("Distance").reset_index(drop=True)
        if len(data) < 3:
            return pd.DataFrame()
        d = data["Distance"].to_numpy()
        s = data["Speed"].to_numpy()
        minima = [i for i in range(1, len(s)-1) if s[i] <= s[i-1] and s[i] < s[i+1]]
        minima.sort(key=lambda i: s[i])
        chosen = []
        for i in minima:
            if all(abs(d[i] - d[j]) >= 120 for j in chosen):
                chosen.append(i)
        return pd.DataFrame([{
            "Lap": label, "Distance (m)": float(d[i]),
            "Minimum speed (km/h)": float(s[i]),
            "Throttle (%)": float(data.iloc[i]["Throttle"])
        } for i in sorted(chosen, key=lambda j: d[j])])

    ca = corner_candidates(lap_a, lap_a_name)
    cb = corner_candidates(lap_b, lap_b_name)
    if ca.empty or cb.empty:
        st.warning("Not enough usable telemetry samples to identify candidate corners in both laps.")
    else:
        b_rows = cb.to_dict("records")
        used = set()
        matches = []
        for _, arow in ca.iterrows():
            options = [(abs(float(brow["Distance (m)"])-float(arow["Distance (m)"])), j, brow)
                       for j, brow in enumerate(b_rows)
                       if j not in used and abs(float(brow["Distance (m)"])-float(arow["Distance (m)"])) <= 150]
            if not options:
                continue
            _, j, brow = min(options, key=lambda item: item[0])
            used.add(j)
            matches.append({
                "Candidate corner": f"Match {len(matches)+1}",
                "Lap A distance (m)": float(arow["Distance (m)"]),
                "Lap B distance (m)": float(brow["Distance (m)"]),
                "Distance offset (B − A, m)": float(brow["Distance (m)"]-arow["Distance (m)"]),
                "Lap A minimum speed (km/h)": float(arow["Minimum speed (km/h)"]),
                "Lap B minimum speed (km/h)": float(brow["Minimum speed (km/h)"]),
                "Minimum speed difference (B − A, km/h)": float(brow["Minimum speed (km/h)"]-arow["Minimum speed (km/h)"]),
                "Lap A throttle (%)": float(arow["Throttle (%)"]),
                "Lap B throttle (%)": float(brow["Throttle (%)"]),
            })
        if not matches:
            st.warning("No candidate corners matched within 150 m. Try another lap pair.")
        else:
            result = pd.DataFrame(matches)
            st.write(f"Matched {len(result)} candidate corners within a 150 m distance tolerance.")
            st.dataframe(result.round(1), use_container_width=True, hide_index=True)
            fig_corner = go.Figure()
            fig_corner.add_trace(go.Scatter(x=result["Candidate corner"], y=result["Lap A minimum speed (km/h)"], mode="lines+markers", name=lap_a_name))
            fig_corner.add_trace(go.Scatter(x=result["Candidate corner"], y=result["Lap B minimum speed (km/h)"], mode="lines+markers", name=lap_b_name))
            fig_corner.update_layout(template="plotly_dark", xaxis_title="Matched candidate corner", yaxis_title="Minimum speed (km/h)", hovermode="x unified")
            st.plotly_chart(fig_corner, use_container_width=True)
            st.download_button(
                "Download corner comparison CSV",
                data=result.to_csv(index=False).encode("utf-8"),
                file_name="corner_by_corner_comparison.csv",
                mime="text/csv",
            )

with tabs[7]:
    st.subheader("Driver performance scorecard")
    st.caption(
        "Side-by-side indicators for the selected laps. These are descriptive telemetry metrics, "
        "not a definitive driver rating; lap conditions and lap type may differ."
    )

    def scorecard_metric(df, column, operation="mean"):
        return metric_value(df, column, operation)

    def brake_on_share(df):
        if "Brake" not in df.columns or df.empty:
            return None
        values = df["Brake"].astype(str).str.strip().str.lower()
        valid = values.isin(["true", "false", "1", "0", "1.0", "0.0"])
        if not valid.any():
            return None
        active = values.isin(["true", "1", "1.0"])
        return float(active[valid].mean() * 100)

    def sector_difference(sector_number):
        if sectors.empty:
            return None
        rows = sectors[sectors["Sector"] == f"Sector {sector_number}"]
        if rows.empty or pd.isna(rows.iloc[0]["Difference (s)"]):
            return None
        return float(rows.iloc[0]["Difference (s)"])

    scorecard_rows = [
        {
            "Metric": "Official sector 1 difference (B − A, s)",
            lap_a_name: sectors.loc[sectors["Sector"] == "Sector 1", "Lap A (s)"].iloc[0]
                if not sectors.empty and (sectors["Sector"] == "Sector 1").any() else np.nan,
            lap_b_name: sectors.loc[sectors["Sector"] == "Sector 1", "Lap B (s)"].iloc[0]
                if not sectors.empty and (sectors["Sector"] == "Sector 1").any() else np.nan,
            "Difference / note": sector_difference(1),
        },
        {
            "Metric": "Official sector 2 difference (B − A, s)",
            lap_a_name: sectors.loc[sectors["Sector"] == "Sector 2", "Lap A (s)"].iloc[0]
                if not sectors.empty and (sectors["Sector"] == "Sector 2").any() else np.nan,
            lap_b_name: sectors.loc[sectors["Sector"] == "Sector 2", "Lap B (s)"].iloc[0]
                if not sectors.empty and (sectors["Sector"] == "Sector 2").any() else np.nan,
            "Difference / note": sector_difference(2),
        },
        {
            "Metric": "Official sector 3 difference (B − A, s)",
            lap_a_name: sectors.loc[sectors["Sector"] == "Sector 3", "Lap A (s)"].iloc[0]
                if not sectors.empty and (sectors["Sector"] == "Sector 3").any() else np.nan,
            lap_b_name: sectors.loc[sectors["Sector"] == "Sector 3", "Lap B (s)"].iloc[0]
                if not sectors.empty and (sectors["Sector"] == "Sector 3").any() else np.nan,
            "Difference / note": sector_difference(3),
        },
        {
            "Metric": "Peak sampled speed (km/h)",
            lap_a_name: scorecard_metric(lap_a, "Speed", "max"),
            lap_b_name: scorecard_metric(lap_b, "Speed", "max"),
            "Difference / note": (
                scorecard_metric(lap_b, "Speed", "max") - scorecard_metric(lap_a, "Speed", "max")
                if scorecard_metric(lap_a, "Speed", "max") is not None
                and scorecard_metric(lap_b, "Speed", "max") is not None else np.nan
            ),
        },
        {
            "Metric": "Mean sampled speed (km/h)",
            lap_a_name: scorecard_metric(lap_a, "Speed", "mean"),
            lap_b_name: scorecard_metric(lap_b, "Speed", "mean"),
            "Difference / note": (
                scorecard_metric(lap_b, "Speed", "mean") - scorecard_metric(lap_a, "Speed", "mean")
                if scorecard_metric(lap_a, "Speed", "mean") is not None
                and scorecard_metric(lap_b, "Speed", "mean") is not None else np.nan
            ),
        },
        {
            "Metric": "High-throttle samples (≥95%, %)",
            lap_a_name: sample_share(lap_a, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95),
            lap_b_name: sample_share(lap_b, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95),
            "Difference / note": (
                sample_share(lap_b, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95)
                - sample_share(lap_a, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95)
                if sample_share(lap_a, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95) is not None
                and sample_share(lap_b, "Throttle", lambda x: pd.to_numeric(x, errors="coerce") >= 95) is not None
                else np.nan
            ),
        },
        {
            "Metric": "Brake-on samples (%)",
            lap_a_name: brake_on_share(lap_a),
            lap_b_name: brake_on_share(lap_b),
            "Difference / note": (
                brake_on_share(lap_b) - brake_on_share(lap_a)
                if brake_on_share(lap_a) is not None and brake_on_share(lap_b) is not None
                else np.nan
            ),
        },
    ]
    scorecard = pd.DataFrame(scorecard_rows)
    st.dataframe(scorecard.round(3), use_container_width=True, hide_index=True)
    st.download_button(
        "Download driver scorecard CSV",
        data=scorecard.to_csv(index=False).encode("utf-8"),
        file_name=f"driver_scorecard_{selection[0]}_{selection[3]}_lap{selection[4]}_vs_lap{selection[5]}.csv",
        mime="text/csv",
    )

    st.info(
        "Interpretation: sector differences are Lap B minus Lap A; negative means Lap B was faster. "
        "Other differences are also B minus A. Speed and throttle/brake sample shares are descriptive only. "
        "No combined score is calculated because these metrics do not by themselves establish fair comparability."
    )

# Build a report from the currently selected telemetry and analysis.
def build_selected_lap_report():
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# F1 Telemetry Lab — Selected Lap Engineering Report",
        "",
        f"- Generated: {generated_at}",
        f"- Season: {selection[0]}",
        f"- Grand Prix: {selection[1]}",
        f"- Session: {selection[2]}",
        f"- Driver: {selected_driver}",
        f"- Lap A: {selection[4]}",
        f"- Lap B: {selection[5]}",
        "",
        "## Overview metrics",
        "",
        "| Metric | Lap A | Lap B |",
        "|---|---:|---:|",
        f"| Telemetry duration (s) | {lap_duration_seconds(lap_a) if lap_duration_seconds(lap_a) is not None else 'Unavailable'} | {lap_duration_seconds(lap_b) if lap_duration_seconds(lap_b) is not None else 'Unavailable'} |",
        f"| Peak sampled speed (km/h) | {metric_value(lap_a, 'Speed') if metric_value(lap_a, 'Speed') is not None else 'Unavailable'} | {metric_value(lap_b, 'Speed') if metric_value(lap_b, 'Speed') is not None else 'Unavailable'} |",
        f"| Mean sampled speed (km/h) | {metric_value(lap_a, 'Speed', 'mean') if metric_value(lap_a, 'Speed', 'mean') is not None else 'Unavailable'} | {metric_value(lap_b, 'Speed', 'mean') if metric_value(lap_b, 'Speed', 'mean') is not None else 'Unavailable'} |",
        f"| High-throttle samples (>=95%, %) | {sample_share(lap_a, 'Throttle', lambda x: pd.to_numeric(x, errors='coerce') >= 95) if 'sample_share' in globals() and sample_share(lap_a, 'Throttle', lambda x: pd.to_numeric(x, errors='coerce') >= 95) is not None else 'Unavailable'} | {sample_share(lap_b, 'Throttle', lambda x: pd.to_numeric(x, errors='coerce') >= 95) if 'sample_share' in globals() and sample_share(lap_b, 'Throttle', lambda x: pd.to_numeric(x, errors='coerce') >= 95) is not None else 'Unavailable'} |",
        "",
        "## Official sector timing (when available)",
        "",
    ]
    if not sectors.empty:
        lines.extend([
            "| Sector | Lap A (s) | Lap B (s) | Difference B − A (s) |",
            "|---|---:|---:|---:|",
        ])
        for _, row in sectors.iterrows():
            def fmt(value):
                return f"{float(value):.3f}" if pd.notna(value) else "Unavailable"
            lines.append(f"| {row['Sector']} | {fmt(row['Lap A (s)'])} | {fmt(row['Lap B (s)'])} | {fmt(row['Difference (s)'])} |")
    else:
        lines.append("Official sector timing was unavailable for this selection.")
    lines.extend([
        "",
        "## Braking and corner-analysis notes",
        "",
        "- Braking events are grouped from consecutive brake-on telemetry samples.",
        "- Candidate corner points are estimated from local speed minima.",
        "- Corner matching is approximate and based on distance along the lap.",
        "- The time-delta plot is an interpolated telemetry estimate, not official timing.",
        "",
        "## Interpretation and limitations",
        "",
        "This report uses sampled historical telemetry. Differences can reflect traffic, tyres, weather, track evolution, lap type and sampling. Local speed minima are not official corner identifiers, and telemetry duration is not the official lap time. Use the results for exploratory learning rather than definitive driver-performance claims.",
    ])
    return "\n".join(lines) + "\n"

selected_report = build_selected_lap_report()
st.subheader("Selected-lap engineering report")
st.caption("Download a Markdown report generated from the current session, driver and lap selections.")
st.download_button(
    "Download selected-lap engineering report",
    data=selected_report.encode("utf-8"),
    file_name=f"f1_report_{selection[0]}_{selection[3]}_lap{selection[4]}_vs_lap{selection[5]}.md",
    mime="text/markdown",
)
# PDF export is generated on demand so a missing PDF dependency cannot break page loading.
if st.button("Prepare PDF engineering report", key="prepare_pdf_report"):
    try:
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, pagesize=A4,
            rightMargin=18*mm, leftMargin=18*mm,
            topMargin=18*mm, bottomMargin=18*mm,
            title="F1 Telemetry Lab Engineering Report",
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ReportTitle", parent=styles["Title"], alignment=TA_LEFT,
            textColor=colors.HexColor("#c8102e"), spaceAfter=10,
        ))
        story = [
            Paragraph("F1 Telemetry Lab", styles["ReportTitle"]),
            Paragraph("Selected-Lap Engineering Report", styles["Heading2"]),
            Spacer(1, 6),
            Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", styles["BodyText"]),
            Spacer(1, 8),
        ]
        session_rows = [
            ["Season", str(selection[0])],
            ["Grand Prix", str(selection[1])],
            ["Session", str(selection[2])],
            ["Driver", str(selected_driver)],
            ["Lap A", str(selection[4])],
            ["Lap B", str(selection[5])],
        ]
        session_table = Table(session_rows, colWidths=[42*mm, 115*mm])
        session_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#eeeeee")),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#bbbbbb")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 7),
            ("RIGHTPADDING", (0,0), (-1,-1), 7),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.extend([session_table, Spacer(1, 14), Paragraph("Overview metrics", styles["Heading2"])])
        def pdf_num(value, digits=3):
            return f"{float(value):.{digits}f}" if value is not None and pd.notna(value) else "Unavailable"
        metrics_rows = [
            ["Metric", lap_a_name, lap_b_name],
            ["Telemetry duration (s)", pdf_num(lap_duration_seconds(lap_a)), pdf_num(lap_duration_seconds(lap_b))],
            ["Peak sampled speed (km/h)", pdf_num(metric_value(lap_a, "Speed"), 1), pdf_num(metric_value(lap_b, "Speed"), 1)],
            ["Mean sampled speed (km/h)", pdf_num(metric_value(lap_a, "Speed", "mean"), 1), pdf_num(metric_value(lap_b, "Speed", "mean"), 1)],
        ]
        metrics_table = Table(metrics_rows, colWidths=[70*mm, 43*mm, 43*mm], repeatRows=1)
        metrics_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#222831")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#bbbbbb")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.extend([metrics_table, Spacer(1, 14), Paragraph("Sector timing", styles["Heading2"])])
        sector_rows = [["Sector", "Lap A (s)", "Lap B (s)", "B − A (s)"]]
        if not sectors.empty:
            for _, row in sectors.iterrows():
                sector_rows.append([
                    str(row["Sector"]), pdf_num(row["Lap A (s)"]),
                    pdf_num(row["Lap B (s)"]), pdf_num(row["Difference (s)"]),
                ])
        else:
            sector_rows.append(["Official sector timing unavailable", "—", "—", "—"])
        sector_table = Table(sector_rows, colWidths=[55*mm, 35*mm, 35*mm, 35*mm], repeatRows=1)
        sector_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#222831")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#bbbbbb")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.extend([
            sector_table, Spacer(1, 14),
            Paragraph("Interpretation and limitations", styles["Heading2"]),
            Paragraph(
                "This report uses sampled historical telemetry. Telemetry duration is not official lap time. "
                "Differences may reflect traffic, tyres, weather, track evolution, lap type and sampling. "
                "Low-speed points and braking events are exploratory indicators, not official corner labels.",
                styles["BodyText"],
            ),
        ])
        doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        st.download_button(
            "Download PDF engineering report",
            data=pdf_bytes,
            file_name=f"f1_report_{selection[0]}_{selection[3]}_lap{selection[4]}_vs_lap{selection[5]}.pdf",
            mime="application/pdf",
            key="download_pdf_report",
        )
    except ImportError:
        st.error("PDF export dependency is missing. Please redeploy after adding reportlab to requirements.txt.")
    except Exception as pdf_error:
        st.error("Could not generate the PDF report.")
        st.caption(str(pdf_error))

with st.expander("Preview selected-lap report"):
    st.markdown(selected_report)

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
