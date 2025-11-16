import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
from scipy.stats import norm

FANTASYNERDS_KEY = "YOUR_FANTASYNERDS_KEY"

# --- Parlay calculation ---
def adjusted_parlay_probability(base_probs, corr_mat):
    z_scores = norm.ppf(base_probs)
    combined_mean = np.sum(z_scores)
    combined_var = np.sum(corr_mat)
    combined_std = np.sqrt(combined_var)
    combined_prob = norm.cdf(combined_mean / combined_std)
    return combined_prob

def load_parlay_config(path="full_depth.json"):
    with open(path) as f:
        data = json.load(f)
    parlay = data.get("parlay_calculator", {})
    base_probs = parlay.get("base_probs", [])
    corr_matrix = parlay.get("correlation_matrix", [])
    return base_probs, corr_matrix

# --- ESPN and Nerds scraping/API code (unchanged) ---
def fetch_espn_team_list():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
        r = requests.get(url)
        teams = r.json().get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
    except Exception as e:
        st.error(f"Error fetching team list from ESPN: {e}")
        return {}
    abbr_to_id = {}
    for t in teams:
        team = t.get("team", {})
        abbr = team.get("abbreviation") or (team.get("displayName") or "")[:3].upper() or "UNK"
        abbr_to_id[abbr] = (team.get("id", "0"), team.get("displayName", abbr))
    return abbr_to_id

def fetch_espn_roster(team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
        r = requests.get(url)
        data = r.json()
    except Exception as e:
        st.error(f"Error fetching roster from ESPN: {e}")
        return [], {}
    roster, pos_map = [], {}
    for group in data.get("athletes", []):
        group_pos = "UNK"
        group_position = group.get("position")
        if isinstance(group_position, dict):
            group_pos = group_position.get("abbreviation") or group_position.get("name") or "UNK"
        items = group.get("items", [])
        if not isinstance(items, list): continue
        for p in items:
            name = p.get("displayName", "Unknown")
            player_pos = group_pos
            player_pos_obj = p.get("position")
            if isinstance(player_pos_obj, dict):
                player_abbr = player_pos_obj.get("abbreviation")
                player_name = player_pos_obj.get("name")
                if player_abbr: player_pos = player_abbr
                elif player_name: player_pos = player_name
            if not player_pos:
                player_pos = "UNK"
            roster.append(name)
            pos_map[name] = player_pos
    return roster, pos_map

def get_nerds_injury(player_name):
    url = f"https://api.fantasynerds.com/v1/nfl/injuries?apikey={FANTASYNERDS_KEY}"
    try:
        r = requests.get(url)
        injuries = r.json().get("injuries", [])
        details = [f"{p.get('status','Healthy')} - {p.get('details','')}" for p in injuries if player_name.lower() in p.get("player", "").lower()]
        return "; ".join(details) if details else "Healthy"
    except Exception as e:
        print(f"Nerds Injury API error: {e}")
    return "Healthy"

def get_nerds_defense_all(team_abbr):
    metrics = {}
    for pos in ["RB", "WR", "TE", "QB"]:
        url = f"https://api.fantasynerds.com/v1/nfl/defense/{pos.lower()}?apikey={FANTASYNERDS_KEY}"
        try:
            r = requests.get(url)
            teams = r.json().get("defense", [])
            for t in teams:
                if t.get("abbr","UNK") == team_abbr:
                    metrics[pos] = t
        except Exception as e:
            print(f"Def API error ({pos}): {e}")
    return metrics

def get_props(player, pos):
    qb_lines = {"Dak Prescott": 270.5, "Josh Allen": 265.5, "Patrick Mahomes": 295.5}
    rb_lines = {"Tony Pollard": 65.5, "Josh Jacobs": 68.0}
    wr_lines = {"CeeDee Lamb": 80.5, "Davante Adams": 77.5}
    te_lines = {"J. Ferguson": 44.0}
    if player in qb_lines and pos == "QB": return qb_lines[player]
    if player in rb_lines and pos == "RB": return rb_lines[player]
    if player in wr_lines and pos == "WR": return wr_lines[player]
    if player in te_lines and pos == "TE": return te_lines[player]
    if pos == "QB": return 245.0
    if pos == "RB": return 54.0
    if pos == "WR": return 49.0
    if pos == "TE": return 34.0
    return 30.0

def get_weather(city, date=None):
    return {"description": "Partly cloudy", "temp": 58, "wind_mph": 9, "precip": 0.1}

# --- MAIN STREAMLIT APP ---

st.title("NFL Prop Analytics: THE ONE FOOTBALL FINAL ENHANCED")

st.markdown("### Prediction Intangibles (Affect Each Player Differently)")
st.write("""
These factors impact every offensive player and are adjustable by both game context and player context:
- Team Defense Quality (overall defense for opponent)
- Defense DVOA Grade (efficiency vs position groups)
- O-Line vs D-Line matchup
- Weather conditions
- Cornerback/Safety Grade (critical for WR projections)
- Matchup strength (WR1 vs CB1, etc)
- Injury status (player-specific)
- Offensive scheme
- Special teams impact, location/city
- Starter/Backup designation
- Usage rate, player role
- Manual adjustment for recent form, usage
- Bot/algorithm/public line comparison (advanced)
""")

team_map = fetch_espn_team_list()
team_abbrs = sorted(team_map.keys())

if "selected" not in st.session_state: st.session_state.selected = []
if "status_msg" not in st.session_state: st.session_state.status_msg = ""

st.markdown("### Team 1")
team1_abbr = st.selectbox("Team 1", team_abbrs, index=0)
team1_id = team_map.get(team1_abbr, ("0", ""))[0]
team1_roster, team1_pos = fetch_espn_roster(team1_id)
players1 = st.multiselect("Players (Team 1)", team1_roster)

st.markdown("### Team 2")
team2_abbr = st.selectbox("Team 2", team_abbrs, index=1)
team2_id = team_map.get(team2_abbr, ("0", ""))[0]
team2_roster, team2_pos = fetch_espn_roster(team2_id)
players2 = st.multiselect("Players (Team 2)", team2_roster)

if st.button("Reset All"):
    st.session_state.selected = []
    st.session_state.status_msg = "Selections cleared. Pick new teams/players and rerun analysis."

if st.button("Run Analysis"):
    st.session_state.selected = (
        [{"name": n, "team": team1_abbr, "pos": team1_pos.get(n, "UNK")} for n in players1] +
        [{"name": n, "team": team2_abbr, "pos": team2_pos.get(n, "UNK")} for n in players2]
    )
    st.session_state.status_msg = ""

if st.session_state.status_msg:
    st.info(st.session_state.status_msg)

# --- BATCH GAME CONTEXT SETTINGS ---
st.markdown("### Game Context (applies to all players)")
batch_defense = st.selectbox("Opponent Team Defense Quality", ["Elite Def", "Solid", "Average", "Below Avg", "Weak"], index=2)
batch_dvoa = st.selectbox("Opponent Defense DVOA Grade", ["Top 5", "Top 10", "Middle", "Bottom 10", "Bottom 5"], index=2)
batch_ol_dl = st.selectbox("O-Line vs D-Line (whole offense)", ["OL Edge", "Even", "DL Edge"], index=1)
batch_weather = st.text_input("Weather Context (all players)", value="Partly cloudy, 58°F, wind 9 mph")

if st.session_state.selected:
    st.header("Player Analytics: Safe/Primary Number")
    results = []
    for ix, p in enumerate(st.session_state.selected, 1):
        st.markdown(f"#### {ix}. **{p['name']}** ({p['team']} - {p['pos']})")
        prop_line = get_props(p["name"], p["pos"])
        opponent = team2_abbr if p["team"] == team1_abbr else team1_abbr
        all_def = get_nerds_defense_all(opponent)
        def_summary = []
        for pos in ["QB", "RB", "WR", "TE"]:
            m = all_def.get(pos, {})
            rank = m.get("rank","—")
            ppg = m.get("points","—")
            def_summary.append(f"{pos}: Rank {rank}, PPG Allowed: {ppg}")
        st.markdown("**FantasyNerds DEF Ranks/PPG:**<br>" + "<br>".join(def_summary), unsafe_allow_html=True)

        injuries = get_nerds_injury(p["name"])
        st.markdown(f"**Injury Status:** {injuries}")
        st.markdown(f"**Vegas/DK Prop Line:** {prop_line}")

        # STARTER/BACKUP/USAGE
        role = st.selectbox("Starter or Backup?", ["Starter", "Backup"], index=0, key=f"role_{ix}")
        usage = st.slider("Usage/Expected Role (Starter=100, Backup/Rotational lower)", min_value=50, max_value=100, value=100 if role=="Starter" else 65, step=1, key=f"usage_{ix}")

        # Individual player intangibles
        cb_grade = st.selectbox("Player CB/Safety Grade", ["Elite", "Solid", "Average", "Weak"], index=2, key=f"cb_{ix}")
        matchup_quality = st.selectbox("Matchup Strength", ["Elite", "Solid", "Average", "Weak"], index=2, key=f"mtch_{ix}")
        injury_est = st.selectbox("Player Injury Status", ["Healthy", "Questionable", "Out"], index=0, key=f"inj_{ix}")
        scheme = st.selectbox("Scheme Impact", ["Man/Blitz", "Zone", "Standard", "Exotic"], index=2, key=f"sch_{ix}")
        form_adj = st.number_input("Manual Adjustment (%)", min_value=-50, max_value=50, value=0, key=f"adj_{ix}")

        # Enhanced projection calculation
        safe_proj = prop_line
        safe_proj *= {"Elite Def":0.85, "Solid":0.92, "Average":1, "Below Avg":1.04, "Weak":1.11}[batch_defense]
        safe_proj *= {"Top 5":0.89, "Top 10":0.93, "Middle":1, "Bottom 10":1.09, "Bottom 5":1.14}[batch_dvoa]
        safe_proj *= {"OL Edge":1.07, "Even":1, "DL Edge":0.93}[batch_ol_dl]
        safe_proj *= usage/100
        safe_proj *= {"Elite":0.88, "Solid":0.94, "Average":1, "Weak":1.05}[cb_grade]
        safe_proj *= {"Elite":0.88, "Solid":0.94, "Average":1, "Weak":1.05}[matchup_quality]
        safe_proj *= {"Healthy":1, "Questionable":0.85, "Out":0.6}[injury_est]
        safe_proj *= {"Man/Blitz":0.96, "Zone":0.98, "Standard":1, "Exotic":1.04}[scheme]
        safe_proj *= 1 + form_adj/100

        st.success(f"Safe Projection: {safe_proj:.1f}")
        st.markdown(f"Weather Context: {batch_weather}")

        # Algorithm/Bot comparison placeholder:
        st.markdown("#### Top 3 Bot/Algorithm Predictions (Compare):")
        st.text("Future: Load & compare with top 3 bot/public lines or projections.")

        results.append({
            "Player": p["name"], "Team": p["team"], "Position": p["pos"], "Role": role, "Usage": usage,
            "Vegas Line": prop_line, "Safe Prompt Output": safe_proj,
            "Nerds DEF Rank QB": all_def.get("QB", {}).get("rank","—"),
            "Nerds DEF Rank RB": all_def.get("RB", {}).get("rank","—"),
            "Nerds DEF Rank WR": all_def.get("WR", {}).get("rank","—"),
            "Nerds DEF Rank TE": all_def.get("TE", {}).get("rank","—"),
            "Injuries": injuries
        })

    if results:
        df = pd.DataFrame(results)
        st.subheader("Batch Analytics Results")
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), file_name="nfl_prop_analytics.csv")
        stats = df["Safe Prompt Output"].describe()
        st.subheader("Safe Projection Stats")
        st.markdown(
            f"**Mean:** {stats['mean']:.2f}  &nbsp;  "
            f"**Median:** {stats['50%']:.2f}  &nbsp;  "
            f"**Std Dev:** {stats['std']:.2f}  &nbsp;  "
            f"**Max:** {stats['max']:.2f}  &nbsp;  "
            f"**Min:** {stats['min']:.2f}"
        )

else:
    st.info("Select teams, players, and click Run Analysis to load analytics interface.")

# --- Parlay section as before ---
st.markdown("---")
st.header("Dynamic Parlay Hit Probability Calculator")

base_probs_loaded, correlation_matrix_loaded = load_parlay_config()
base_probs_input = [
    st.number_input(f"Leg {i+1} Hit Probability (0.00 - 1.00)", min_value=0.0, max_value=1.0, value=default, format="%.2f")
    for i, default in enumerate(base_probs_loaded)
]
corr_df = pd.DataFrame(
    correlation_matrix_loaded,
    columns=[f"Leg {i+1}" for i in range(len(correlation_matrix_loaded))],
    index=[f"Leg {i+1}" for i in range(len(correlation_matrix_loaded))]
)
edited_corr_df = st.data_editor(corr_df, num_rows="dynamic")
for i in range(len(edited_corr_df)):
    edited_corr_df.iat[i, i] = 1.0
    for j in range(i + 1, len(edited_corr_df)):
        val = (edited_corr_df.iat[i, j] + edited_corr_df.iat[j, i]) / 2
        edited_corr_df.iat[i, j] = val
        edited_corr_df.iat[j, i] = val
if st.button("Calculate Parlay Hit Probability"):
    base_probs = np.array(base_probs_input)
    correlation_matrix = edited_corr_df.values
    parlay_prob = adjusted_parlay_probability(base_probs, correlation_matrix)
    st.success(f"Parlay Hit Probability (Adjusted for Correlation): {parlay_prob:.2%}")