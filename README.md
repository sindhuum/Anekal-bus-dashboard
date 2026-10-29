# Anekal Public Transportation Dashboard (Streamlit)

Shows how well BMTC city buses serve Anekal: login, 3 filter menus (Area, Time of day, Route), charts, insights and conclusion.

## Run on your computer
    pip install -r requirements.txt
    streamlit run app.py
Demo login: `anekal` / `Bus@2026` (change it with Streamlit secrets, see `.streamlit/secrets.toml.example`).

## Deploy (Streamlit Community Cloud)
1. Upload these files to a GitHub repository.
2. At share.streamlit.io choose New app, pick the repository, set main file to `app.py`.
3. Optional: App settings -> Secrets, add USERNAME and PASSWORD.

Data: BMTC GTFS (community feed), filtered to Anekal and pre-aggregated in `data/anekal.json`. Scheduled trips for one day, not live tracking.
