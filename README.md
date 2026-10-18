# 🏎️ F1 Telemetry Lab — Formula 1 Lap Analysis

An interactive motorsport engineering and data-analysis project built with Python to explore historical Formula 1 telemetry, compare laps, visualize driver inputs, and investigate performance differences.

**🚀 [Launch the Live Dashboard](https://f1-lap-telemetry.streamlit.app/)** · **💻 [View Source Code](https://github.com/yazdaanwali/f1-lap-telemetry-analysis)**

---

## 📌 Project Overview

F1 Telemetry Lab is an interactive dashboard for analysing historical Formula 1 lap data. Users can select a season, Grand Prix, session, driver, and two laps, then explore telemetry visualizations and engineering indicators.

The project demonstrates how data processing, visualization, and automated data-quality checks can support motorsport analysis.

## ✨ Key Features

### 1. Dynamic Historical Session Selection
- Select available seasons, Grand Prix events, and session types.
- Choose drivers and laps based on the data returned by the provider.
- Compare two different laps from the same selected driver.
- Handle unavailable sessions and missing data with warnings.

### 2. Telemetry Visualization
- Speed versus distance comparison.
- Synchronized telemetry comparisons where signals are available.
- Throttle position, braking, engine RPM, and gear analysis.
- Sampled peak speed and mean speed statistics.

### 3. Circuit Visualization
- Visualize source X/Y position coordinates.
- Explore braking locations and low-speed regions.
- Investigate approximate corner locations using telemetry data.

### 4. Sector Timing and Time-Delta Analysis
- Compare sector times when official timing fields are available.
- Calculate time differences over the shared distance range.
- Export supported sector and time-delta analysis tables as CSV files.

### 5. Braking and Corner Analysis
- Identify approximate braking events from consecutive brake-on samples.
- Examine braking-event distance, entry speed, minimum speed, and throttle at event end.
- Explore low-speed points and approximate corner matches between laps.

### 6. Driver Performance Scorecard
- Compare available sector times.
- Examine peak and mean sampled speeds.
- Review high-throttle and brake-on sample percentages.
- Export supported scorecard data to CSV.

These metrics describe the selected telemetry; they do not establish an overall driver ranking or prove the cause of a performance difference.

### 7. Automated Data-Quality Screening
- Detect missing or invalid distance, speed, and timestamp values.
- Flag duplicate distance samples and backwards distance progression.
- Flag negative speeds and sampled speeds above 400 km/h for verification.
- Check telemetry sample counts, distance coverage, timestamp ordering, and sector-time availability.
- Highlight unusually large sector-time differences.

Quality flags are screening indicators, not official FIA lap classifications. Duplicate samples and unusual values should be investigated rather than automatically treated as proof of invalid data.

### 8. Engineering Reports and Exports
- Download a Markdown analysis report.
- Generate a PDF engineering report.
- Export supported comparison tables as CSV files.
- Review selected session details, available metrics, sector timings, and methodological limitations.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and analysis logic |
| Streamlit | Interactive web dashboard |
| pandas | Data processing and tabular analysis |
| NumPy | Numerical calculations |
| Plotly | Interactive charts and visualizations |
| TIF1 | Historical session and telemetry data retrieval |
| ReportLab | PDF report generation |
| Matplotlib | Supporting plotting and exploratory analysis |
| Jupyter Notebook | Exploratory analysis and experimentation |
| GitHub Actions | Automated validation and unit tests |

## 🖥️ Run the Project Locally

### Prerequisites

- Python 3.12 recommended for the project's validation workflow.
- Git.
- Internet access for historical telemetry retrieval.

### Step 1: Clone the repository

```bash
git clone https://github.com/yazdaanwali/f1-lap-telemetry-analysis.git
cd f1-lap-telemetry-analysis
```

### Step 2: Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 4: Launch the dashboard

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

The first data request may take some time. Available events, drivers, laps, and telemetry signals depend on the data provider.

## 📂 Repository Structure

```text
f1-lap-telemetry-analysis/
│
├── app.py
├── analysis.py
├── lap_telemetry_analysis.ipynb
├── requirements.txt
├── README.md
│
├── tests/
│   └── test_analysis_helpers.py
│
├── .github/
│   └── workflows/
│       └── validate.yml
│
├── data/
├── figures/
└── reports/
```

Generated files and additional data may vary as the project develops.

## 🔬 Analysis Methodology

1. Retrieve the selected historical session and lap telemetry.
2. Prepare numeric telemetry channels for analysis.
3. Compare speed and other signals against distance.
4. Align telemetry over a shared distance range for time-delta analysis.
5. Compare sector timing values when available.
6. Identify approximate braking events and low-speed regions.
7. run data-quality screening checks and present review warnings.
8. Generate reports and exports from the selected analysis.

Automated outputs are intended to support exploration and interpretation, not replace engineering verification.

## 🧪 Testing and Validation

The repository includes GitHub Actions validation for:

- Python syntax compilation.
- Unit tests for selected analysis helper functions.
- Regression tests for telemetry-duration calculations.
- Regression tests for telemetry-quality screening.
- Expected dashboard sections and dependency declarations.

**[View GitHub Actions](https://github.com/yazdaanwali/f1-lap-telemetry-analysis/actions)**

Automated tests cover defined cases; they do not guarantee that every historical session or provider response will work.

## ⚠️ Limitations

- This is an educational analysis project, not a live F1 timing system.
- Historical telemetry coverage varies by season, event, session, driver, and signal.
- Telemetry duration is calculated from the available timestamps and is not necessarily the official lap time.
- Sampled speed, throttle, and braking statistics depend on the available data and sampling resolution.
- Traffic, tyre condition, weather, fuel load, track evolution, lap type, and other factors can affect lap comparisons.
- Source X/Y coordinates are not surveyed geographic coordinates.
- Low-speed points are only candidates for corner-apex regions; approximate corner matching may be inaccurate.
- Data-quality checks flag suspicious patterns but cannot independently establish whether a lap was a clean flying lap.
- The PDF report does not currently embed interactive Plotly charts.

## 🎯 Project Goals

- Develop practical Python and data-analysis skills.
- Explore telemetry interpretation and motorsport engineering concepts.
- Build a reproducible, interactive engineering-analysis workflow.
- Improve data validation, visualization, and technical reporting.

## 👨‍💻 Author

**Mohammad Yazdaan Wali Khan**

B.Tech Electronics and Communication Engineering student interested in motorsport engineering, telemetry analysis, embedded systems, and engineering data visualization.

## 📄 Disclaimer

This is an independent educational project. It is not affiliated with, endorsed by, or sponsored by Formula 1, the FIA, or any Formula 1 team. All trademarks belong to their respective owners.

---

⭐ If you find this project useful, consider starring the repository or sharing feedback through GitHub.
