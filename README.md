# F1 Telemetry Lab — Lap Telemetry Analysis

An educational motorsport data-analysis project for exploring and comparing historical Formula 1 telemetry. Built with Python, pandas, NumPy, Plotly, TIF1 and Streamlit.

**[Launch the live dashboard](https://f1-lap-telemetry.streamlit.app/)**

## Project overview

F1 Telemetry Lab lets you select a historical session and compare two laps from the same driver. The dashboard retrieves telemetry for your selection and updates its visualizations and analysis accordingly.

### Interactive controls

- Season
- Grand Prix
- Session type
- Driver
- Lap A and Lap B

The available combinations depend on the telemetry provider and the data it has available. If a session, driver, lap, or timing field is unavailable, the dashboard may show a warning rather than a result.

## Features

### 1. Overview and telemetry
- Speed versus distance for both selected laps
- Sampled peak-speed and mean-speed comparisons
- Synchronized speed, throttle, brake, RPM and gear traces where signals are available
- Automatic indicators for high-throttle samples and brake-on samples

### 2. Circuit position
- Plot of the source's X/Y position coordinates
- Overlay of brake-on samples
- Candidate low-speed points estimated from local speed minima

### 3. Sector and time-delta analysis
- Official sector timing comparison when the provider supplies the required fields
- Interpolated elapsed-time delta over the laps' common distance range
- Downloadable time-delta and sector comparison CSVs when available

### 4. Braking and corner exploration
- Grouping of consecutive brake-on samples into approximate braking events
- Entry speed, minimum speed during an event, event distance and throttle at event end
- Candidate low-speed points that may indicate corner-apex regions
- Approximate corner matching between laps based on distance

### 5. Engineering reports
- Downloadable Markdown report generated from the current selection
- PDF report with session details, overview metrics and available sector timing
- CSV exports for selected analysis tables

## Technology stack

- **Python** — analysis and data processing
- **Streamlit** — interactive dashboard
- **pandas / NumPy** — telemetry preparation and calculations
- **Plotly** — interactive charts
- **TIF1** — historical session and telemetry retrieval
- **ReportLab** — PDF report generation
- **Jupyter Notebook** — exploratory analysis

## Run locally

### 1. Get the repository

```bash
git clone https://github.com/yazdaanwali/f1-lap-telemetry-analysis.git
cd f1-lap-telemetry-analysis
```

### 2. Create and activate a virtual environment (recommended)

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the commands below using the environment's Python executable directly.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the dashboard

```bash
python -m streamlit run app.py
```

Open the local address Streamlit prints in the terminal, usually `http://localhost:8501`.

Historical telemetry retrieval requires an internet connection and a functioning compatible data provider. The first request for a session may take time to load.

## Repository structure

```text
f1-lap-telemetry-analysis/
├── app.py
├── analysis.py
├── lap_telemetry_analysis.ipynb
├── requirements.txt
├── README.md
├── data/
├── figures/
└── reports/
    └── lap_analysis_report.md
```

Exact files and generated outputs may differ as the project evolves. Some legacy CSVs and figures are retained for offline analysis; the interactive dashboard uses the currently selected session for its dynamic telemetry views.

## Methodology

- Telemetry signals are plotted against distance for lap-to-lap comparison.
- Sector comparisons use timing values returned by the data source when available.
- The time-delta plot interpolates elapsed telemetry time onto a shared distance grid over the common distance range.
- Braking events are grouped from consecutive brake-on samples.
- Candidate low-speed points are found using local minima and spaced to reduce dense clusters.
- Candidate corner matches use distance proximity; they are exploratory, not official corner identification.

## Important limitations

- This is a historical educational project, not a live F1 timing system.
- Telemetry duration is not necessarily the official lap time.
- Sampled peak speed, mean speed, throttle share and brake share are descriptive indicators, not standalone measures of driver performance.
- Traffic, tyres, weather, track evolution, lap type and sampling differences can affect comparisons.
- X/Y coordinates are source coordinates, not a surveyed geographic circuit map.
- Local speed minima are not guaranteed to be corner apexes, and distance-based matching can pair the wrong points.
- Official sector times and signals may be missing for some sessions or laps.
- The PDF report currently includes session details, overview metrics and available sector timings; it does not embed Plotly charts.

## Disclaimer

This is an independent educational project. It is not affiliated with, endorsed by, or sponsored by Formula 1 or any racing team.
