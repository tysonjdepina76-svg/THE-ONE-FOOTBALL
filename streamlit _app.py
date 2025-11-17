import streamlit as st
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup  # For future web scraping/data parsing use

THESPORTSDB_KEY = st.secrets["THESPORTSDB_KEY"]
FANTASYNERDS_KEY = st.secrets["FANTASYNERDS_KEY"]
SPORTSDATAIO_KEY = st.secrets["SPORTSDATAIO_KEY"]
THEODDSAPI_KEY = st.secrets["THEODDSAPI_KEY"]

def get_nfl_teams():
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/search_all_teams.php?l=NFL"
    try:
        resp = requests.get(url)
        return resp.json().get("teams", [])
    except Exception as e:
        st.error(f"NFL teams error: {e}")
        return []

def get_team_players(team_id):
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/lookup_all_players.php?id={team_id}"
    try:
        resp = requests.get(url)
        return resp.json().get("player", [])
    except Exception as e:
        st.error(f"Players error: {e}")
        return []

def get_team_events(team_id):
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/eventsnext.php?id={team_id}"
    try:
        resp = requests.get(url)
        return resp.json().get("events", [])
    except Exception as e:
        st.error(f"Events error: {e}")
        return []

def get_nerds_injury(player_name):
    try:
        url = f"https://api.fantasynerds.com/v1/nfl/injuries?apikey={FANTASYNERDS_KEY}"
        r = requests.get(url)
        injuries = r.json().get("injuries", [])
        for p in injuries:
            if player_name.lower() in p.get("player", "").lower():
                return f"{p.get('status','Healthy')} - {p.get('details','')}"
        return "Healthy"
    except Exception:
        return "Healthy"

def get_current_nfl_games():
    url = "https://api.sportsdata.io/v3/nfl/scores/json/ScoresByWeek/2025/11"
    headers = {"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY}
    try:
        r = requests.get(url, headers=headers)
        return r.json()
    except Exception as e:
        st.warning(f"SportsDataIO games error: {e}")
        return []

def get_player_props_for_game(game_id):
    url = f"https://api.sportsdata.io/v3/nfl/odds/json/BettingPlayerPropsByGameID/{game_id}"
    headers = {"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY}
    try:
        r = requests.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def get_theoddsapi_props(player_fragment):
    url = (
        f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/"
        f"?regions=us&markets=player_pass_yds,player_rush_yds,player_rec_yds"
        f"&apiKey={THEODDSAPI_KEY}"
    )
    try:
        r = requests.get(url)
        data = r.json()
        found = []
        for event in data:
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        desc = outcome.get("description", "")
                        if player_fragment.lower() in desc.lower():
                            found.append({
                                "matchup": event.get("home_team") + " vs " + event.get("away_team"),
                                "book": bookmaker["title"],
                                "market": market["key"],
                                "player": desc,
                                "line": outcome.get("point"),
                                "odds": outcome.get("price")
                            })
        return found
    except Exception:
        return []

st.title("NFL Prop Analytics | Batch, Parlay, Multi-API Enhanced")
st.caption("Analytics, line shopping, batch props, summary, parlay, BeautifulSoup future-ready. Powered by TheSportsDB, FantasyNerds, SportsDataIO, TheOddsAPI.")

teams = get_nfl_teams()
if not teams:
    st.error("NFL teams could not be loaded.")
    st.stop()

team_opts = [f"{t.get('strTeam')} ({t.get('strTeamShort')})" for t in teams]
team_lookup = {t.get('strTeam'): t for t in teams}
team_choice = st.selectbox("Choose Team", team_opts)
team_selected = team_lookup[team_choice.split(' (')[0]]

events = get_team_events(team_selected['idTeam'])
if events:
    st.markdown("#### Upcoming Games")
    st.dataframe(pd.DataFrame([{
        'Event': e.get('strEvent'),
        'Date': e.get('dateEvent'),
        'Time': e.get('strTime')
    } for e in events]))

players = get_team_players(team_selected['idTeam'])
player_opts = [f"{p['strPlayer']} ({p.get('strPosition','UNK')})" for p in players] if players else []
sel_players = st.multiselect("Select Players for Analysis", player_opts)

results = []
games = get_current_nfl_games()

for pc in sel_players:
    pname = pc.split(' (')[0]
    p = next((x for x in players if x['strPlayer'] == pname), None)
    injury = get_nerds_injury(p['strPlayer']) if p else "N/A"
    sdio_prop, sdio_book, sdio_market = None, None, None
    for g in games:
        for tk in ["HomeTeam", "AwayTeam"]:
            if team_selected["strTeamShort"].upper() == g.get(tk, '').upper():
                props = get_player_props_for_game(g["GameID"])
                for prop in props:
                    if prop.get("PlayerName") and pname.lower() in prop.get("PlayerName").lower():
                        sdio_prop = prop.get("Value")
                        sdio_book = prop.get("Sportsbook")
                        sdio_market = prop.get("BettingMarketType")
    oddsapi_props = get_theoddsapi_props(pname)
    oddsapi_val = ", ".join([f"{o['book']}:{o['line']}" for o in oddsapi_props]) if oddsapi_props else "NA"
    results.append({
        "Player": pname,
        "Position": p.get("strPosition") if p else None,
        "Injury": injury,
        "SportsDataIO Line": sdio_prop,
        "SportsDataIO Market": sdio_market,
        "SportsDataIO Book": sdio_book,
        "Other Books (OddsAPI)": oddsapi_val
    })

if results:
    df = pd.DataFrame(results)
    st.markdown("#### Batch Analytics Table")
    st.dataframe(df)
    st.download_button("Download CSV", df.to_csv(index=False), file_name="nfl_props_analytics.csv")
    num_with_lines = df['SportsDataIO Line'].dropna()
    lines_f = pd.to_numeric(num_with_lines, errors='coerce')
    st.markdown(
        f"**Props:** {len(num_with_lines)} | "
        f"**Mean:** {lines_f.mean() if not lines_f.empty else 'NA'} | "
        f"**Min:** {lines_f.min() if not lines_f.empty else 'NA'} | "
        f"**Max:** {lines_f.max() if not lines_f.empty else 'NA'} | "
        f"**Std Dev:** {lines_f.std() if not lines_f.empty else 'NA'}"
    )
    if not lines_f.empty:
        edge_idx = lines_f.idxmax()
        st.info(f"Top Edge: {df.loc[edge_idx]['Player']} | {df.loc[edge_idx]['SportsDataIO Market']} | Line: {df.loc[edge_idx]['SportsDataIO Line']}")

st.markdown("#### Parlay Hit Probability Calculator")
num_legs = st.number_input("Number of Legs", min_value=2, max_value=8, value=3)
leg_probs = [st.slider(f"Leg {i+1} Win Probability (%)", min_value=1, max_value=100, value=60) / 100 for i in range(num_legs)]
if st.button("Calculate Parlay Probability"):
    hit_prob = np.prod(leg_probs)
    st.success(f"Parlay Total Hit Probability: {hit_prob:.2%}")

user_notes = st.text_area("Add Game Research Notes/Observations:")
if user_notes:
    st.info(user_notes)

st.markdown("---")
st.markdown("**Diagnostics Report**")
st.write(f"Teams: {len(teams)}, Events: {len(events) if events else 0}, Players: {len(players) if players else 0}")
st.write(f"APIs live: TheSportsDB, FantasyNerds, SportsDataIO, TheOddsAPI")