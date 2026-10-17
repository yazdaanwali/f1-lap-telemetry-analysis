# F1 Lap Telemetry Analysis

An educational motorsport data analysis project that compares two
historical Formula 1 qualifying laps using Python, pandas, Plotly,
and Streamlit.


## Live dashboard

**[Open the F1 Telemetry Lab dashboard](https://f1-lap-telemetry-analysis-kasnbcyhjpk4aehrvxmenc.streamlit.app/)**

Explore interactive speed, throttle, braking, RPM, gear, circuit-position,
sector-time, and elapsed-time-delta visualizations.

## Dashboard

The interactive dashboard provides:

- Speed versus distance comparison for two laps
- Telemetry traces for speed, throttle, braking, RPM, and gear
- X/Y circuit-position visualization
- Sector-by-sector time comparison
- An interpolated elapsed-time delta chart
- Downloadable sector and time-delta data
- Access to the generated Markdown analysis report

## Data used

The current comparison uses historical qualifying telemetry from
the 2024 British Grand Prix:

- Driver: Max Verstappen (VER)
- Lap A: lap 23 — 86.203 seconds
- Lap B: lap 20 — 86.350 seconds
- Lap-time difference: Lap B was 0.147 seconds slower

These values describe this specific comparison and are not a
general measure of driver performance.

## Technology stack

- Python
- Streamlit
- Plotly
- pandas
- NumPy
- Matplotlib
- TIF1 telemetry library
- Jupyter Notebook

## Run locally

### 1. Install Python

Use a supported Python version compatible with the packages
listed in `requirements.txt`.

### 2. Open the project directory

```bash
cd Lap-Telemetry-Analysis
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Launch the dashboard

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually
`http://localhost:8501`.

The dashboard reads the saved telemetry CSVs from `data/`
and the sector comparison from `figures/`.

## Project structure

```text
Lap-Telemetry-Analysis/
├── app.py
├── analysis.py
├── lap_telemetry_analysis.ipynb
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── lap_a_telemetry.csv
│   ├── lap_b_telemetry.csv
│   └── cache/
├── figures/
│   ├── lap_speed_comparison.png
│   ├── lap_telemetry_analysis.png
│   ├── sector_analysis.csv
│   └── sector_comparison.png
└── reports/
    └── lap_analysis_report.md
```

## Methodology

Telemetry is plotted against distance for lap-to-lap comparison.
Sector differences are calculated from saved sector timing data.
The time-delta chart interpolates elapsed time onto a shared
distance grid over the laps' common distance range.

## Limitations

- This is a historical analysis project, not a live F1 telemetry
  system.
- Lap comparisons can be affected by track conditions, tyres,
  traffic, and other session variables.
- The X/Y plot visualizes source position coordinates; it is not
  a surveyed geographic map.
- The interpolated time-delta chart is an estimate based on
  sampled telemetry, not official timing at every distance.
- Reproducing the original data retrieval may require a working
  network connection and a compatible telemetry data source.

## Disclaimer

This is an independent educational project. It is not affiliated
with, endorsed by, or sponsored by Formula 1 or any racing team.
