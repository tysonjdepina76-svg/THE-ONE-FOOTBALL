# THE ONE FOOTBALL – NFL Prop Analyzer

This app runs the NFL FINAL TEMPLATE for any game:
- Pulls baseline projections and matchup data from your APIs.
- Adjusts for DVOA, pressure, coverage, injuries, and game script.
- Outputs a player table you can download and use for props and parlays.

## Local setup

1. Install packages:

   pip install -r requirements.txt

2. Create a `.env` file in this folder:

   SPORTSDATAIO_API_KEY=your_sportsdataio_key_here
   DVOA_API_KEY=your_dvoa_key_here
   INJURY_API_KEY=your_injury_key_here
   ADVANCED_METRICS_API_KEY=your_adv_metrics_key_here

3. Run the app:

   streamlit run streamlit_app.py

## Streamlit Cloud

1. Push this folder to GitHub.
2. In Streamlit Cloud, set the entry file to `streamlit_app.py`.
3. Put any keys you want in `.streamlit/secrets.toml` (optional).
4. Deploy and use the app on your phone or desktop.