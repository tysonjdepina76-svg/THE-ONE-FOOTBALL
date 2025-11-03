import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="THE ONE FOOTBALL v8.0", page_icon="🏈", layout="wide")

st.markdown("""
<style>
.stButton button {width: 100%; border-radius: 8px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

NFL_TEAMS = sorted(["Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"])

POSITIONS = ["QB", "RB", "WR", "TE"]

POSITION_STATS = {
    "QB": ["passing_yards", "passing_tds", "rushing_yards", "rushing_tds"],
    "RB": ["rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds"],
    "WR": ["receiving_yards", "receiving_tds", "receptions"],
    "TE": ["receiving_yards", "receiving_tds", "receptions"]
}

STATS_CONFIG = {
    "passing_yards": {"name": "Passing Yards", "base": 250, "variance": 30},
    "passing_tds": {"name": "Passing TDs", "base": 1.5, "variance": 0.5},
    "rushing_yards": {"name": "Rushing Yards", "base": 65, "variance": 20},
    "rushing_tds": {"name": "Rushing TDs", "base": 0.5, "variance": 0.4},
    "receiving_yards": {"name": "Receiving Yards", "base": 55, "variance": 18},
    "receiving_tds": {"name": "Receiving TDs", "base": 0.4, "variance": 0.3},
    "receptions": {"name": "Receptions", "base": 5.5, "variance": 1.5}
}

DEFENSE_RANKINGS = {
    "Arizona Cardinals": {"pass": 28, "run": 22}, "Dallas Cowboys": {"pass": 11, "run": 16},
    "Baltimore Ravens": {"pass": 8, "run": 5}, "Buffalo Bills": {"pass": 12, "run": 10},
    "Kansas City Chiefs": {"pass": 13, "run": 12}, "San Francisco 49ers": {"pass": 2, "run": 2}
}

POPULAR_PLAYERS = {
    "QB": ["Dak Prescott", "Kyler Murray", "Patrick Mahomes", "Josh Allen"],
    "RB": ["Javonte Williams", "Bam Knight", "Saquon Barkley"],
    "WR": ["CeeDee Lamb", "Marvin Harrison Jr.", "George Pickens", "Tyreek Hill"],
    "TE": ["Jake Ferguson", "Trey McBride", "Travis Kelce"]
}

if 'games' not in st.session_state:
    st.session_state.games = []
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'game_conditions' not in st.session_state:
    st.session_state.game_conditions = {}
if 'current_game' not in st.session_state:
    st.session_state.current_game = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

def calculate_defense_factor(opponent, stat_type):
    defense_type = "pass" if any(x in stat_type for x in ["passing", "receiving", "receptions"]) else "run"
    rank = DEFENSE_RANKINGS.get(opponent, {}).get(defense_type, 16)
    if rank <= 5:
        return 0.80
    elif rank <= 10:
        return 0.88
    elif rank <= 16:
        return 0.95
    elif rank <= 24:
        return 1.0
    elif rank <= 28:
        return 1.12
    else:
        return 1.18

def calculate_projection(player, position, stat, opponent, is_home, game_id):
    cfg = STATS_CONFIG[stat]
    base = cfg['base']
    variance = cfg['variance']
    
    adjustments = {
        ("QB", "rushing_yards"): 25, ("QB", "rushing_tds"): 0.3,
        ("RB", "rushing_yards"): 75, ("RB", "receiving_yards"): 30,
        ("WR", "receiving_yards"): 65, ("WR", "receptions"): 6.0,
        ("TE", "receiving_yards"): 45, ("TE", "receptions"): 5.0
    }
    base = adjustments.get((position, stat), base)
    
    defense_factor = calculate_defense_factor(opponent, stat)
    home_factor = 1.07 if is_home else 1.0
    
    conditions = st.session_state.game_conditions.get(game_id, {})
    total = conditions.get('total', 45)
    
    if total >= 50:
        script_factor = 1.12
    elif total >= 47:
        script_factor = 1.08
    elif total >= 44:
        script_factor = 1.04
    else:
        script_factor = 1.0
    
    projection = base * defense_factor * home_factor * script_factor
    line = max(0, np.random.normal(projection, variance * 0.15))
    target = line * (1 + np.random.uniform(0.06, 0.14))
    
    base_confidence = 65
    if defense_factor > 1.15:
        base_confidence += 10
    elif defense_factor < 0.85:
        base_confidence -= 10
    if is_home:
        base_confidence += 3
    if script_factor > 1.08:
        base_confidence += 5
    
    confidence = np.clip(base_confidence + np.random.uniform(-3, 3), 55, 85)
    
    return {
        'player': player, 'position': position, 'stat': STATS_CONFIG[stat]['name'],
        'line': round(line, 1), 'target': round(target, 1), 'margin': round(target - line, 1),
        'confidence': round(confidence, 1), 'opponent': opponent, 'is_home': is_home
    }

def get_parlay_odds(legs):
    odds_map = {
        2: ("+264", 2.64), 3: ("+596", 5.96), 4: ("+1228", 11.28),
        5: ("+2435", 23.35), 6: ("+4700", 47.0), 7: ("+7500", 75.0),
        8: ("+9500", 95.0), 9: ("+15000", 150.0), 10: ("+25000", 250.0),
        11: ("+35000", 350.0), 12: ("+40000", 400.0)
    }
    return odds_map.get(legs, ("+40000", 400.0))

st.markdown("""
<div style='text-align: center; background: linear-gradient(135deg, #1f5156 0%, #2a7d87 100%); 
     color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
    <h1>🏈 THE ONE FOOTBALL v8.0</h1>
    <p>⚡ Built to Win 💰</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("Games", len(st.session_state.games))
col2.metric("Props", len(st.session_state.analysis_results))
col3.metric("Version", "8.0")

tab1, tab2, tab3 = st.tabs(["🏟️ Setup", "👥 Players", "📊 Results"])

with tab1:
    st.header("Game Setup")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Create Game")
        away = st.selectbox("Away", [""] + NFL_TEAMS, key="away")
        home = st.selectbox("Home", [""] + NFL_TEAMS, key="home")
        
        if st.button("Create", type="primary"):
            if away and home and away != home:
                game = f"{away} @ {home}"
                if game not in st.session_state.games:
                    st.session_state.games.append(game)
                    st.session_state.players[game] = []
                    st.success(f"✅ {game}")
                    st.rerun()
    
    with c2:
        st.subheader("Conditions")
        if st.session_state.games:
            sel = st.selectbox("Game", st.session_state.games)
            total = st.number_input("O/U", 30.0, 65.0, 48.5, 0.5)
            spread = st.number_input("Spread", -20.0, 20.0, -7.5, 0.5)
            
            if st.button("Activate", type="primary"):
                st.session_state.game_conditions[sel] = {'total': total, 'spread': spread}
                st.session_state.current_game = sel
                st.success("✅ Active")
                st.rerun()

with tab2:
    st.header("Add Players")
    
    if not st.session_state.current_game:
        st.warning("Set up game first")
    else:
        teams = st.session_state.current_game.split(" @ ")
        
        c1, c2 = st.columns(2)
        with c1:
            team = st.selectbox("Team", teams)
            method = st.radio("Method", ["Quick", "Manual"], horizontal=True)
            
            if method == "Quick":
                pos = st.selectbox("Position", POSITIONS, key="qpos")
                name = st.selectbox("Player", POPULAR_PLAYERS[pos], key="qname")
            else:
                pos = st.selectbox("Position", POSITIONS, key="mpos")
                name = st.text_input("Name", key="mname")
            
            if st.button("ADD & ANALYZE", type="primary"):
                if name:
                    if st.session_state.current_game not in st.session_state.players:
                        st.session_state.players[st.session_state.current_game] = []
                    
                    existing = [p['name'] for p in st.session_state.players[st.session_state.current_game]]
                    if name not in existing:
                        st.session_state.players[st.session_state.current_game].append({'name': name, 'position': pos, 'team': team})
                        
                        is_home = (team == teams[1])
                        opponent = teams[1] if team == teams[0] else teams[0]
                        
                        for stat in POSITION_STATS[pos]:
                            result = calculate_projection(name, pos, stat, opponent, is_home, st.session_state.current_game)
                            st.session_state.analysis_results.append(result)
                        
                        st.success(f"✅ {name}")
                        st.rerun()
        
        with c2:
            st.subheader("Players")
            if st.session_state.current_game in st.session_state.players:
                for i, p in enumerate(st.session_state.players[st.session_state.current_game]):
                    co1, co2, co3 = st.columns([3, 2, 1])
                    co1.write(f"**{p['name']}**")
                    co2.write(f"{p['position']}")
                    if co3.button("🗑️", key=f"d{i}"):
                        removed = st.session_state.players[st.session_state.current_game][i]['name']
                        st.session_state.players[st.session_state.current_game].pop(i)
                        st.session_state.analysis_results = [r for r in st.session_state.analysis_results if r['player'] != removed]
                        st.rerun()

with tab3:
    st.header("Results")
    
    if not st.session_state.analysis_results:
        st.info("Add players first")
    else:
        threshold = st.slider("Min Confidence", 50, 85, 60, 5)
        filtered = [r for r in st.session_state.analysis_results if r['confidence'] >= threshold]
        
        st.markdown(f"### ✅ {len(filtered)} Props")
        
        if filtered:
            for r in filtered:
                emoji = "🟢" if r['confidence'] >= 70 else "🟡"
                with st.expander(f"{emoji} {r['player']} - {r['stat']} | {r['confidence']}%"):
                    ca, cb, cc = st.columns(3)
                    ca.metric("Line", r['line'])
                    cb.metric("Target", r['target'], f"+{r['margin']}")
                    cc.metric("Conf", f"{r['confidence']}%")
            
            if len(filtered) >= 2:
                st.markdown("---")
                st.markdown("## 💰 Parlay")
                
                legs = st.slider("Legs", 2, min(12, len(filtered)), 6)
                parlay = filtered[:legs]
                prob = np.prod([p['confidence']/100 for p in parlay]) * 100
                odds_str, mult = get_parlay_odds(legs)
                
                ca, cb, cc = st.columns(3)
                ca.metric("Probability", f"{prob:.2f}%")
                cb.metric("Odds", odds_str)
                cc.metric("EV", f"{((prob/100*mult-1)*100):+.0f}%")
                
                st.markdown("### Your Parlay:")
                for i, p in enumerate(parlay, 1):
                    st.markdown(f"{i}. **{p['player']}** OVER **{p['line']}** {p['stat']}")
                
                bet = st.number_input("Bet Amount", 10, 1000, 100, 10)
                st.success(f"**Win: ${bet * mult:,.0f}**")
                
                st.markdown("### Copy to Sportsbook:")
                parlay_text = "
".join([f"{i}. {p['player']} OVER {p['line']} {p['stat']}" for i, p in enumerate(parlay, 1)])
                st.code(parlay_text)

st.markdown("---")
st.markdown("<div style='text-align: center;'>🏈 THE ONE FOOTBALL v8.0 FINAL</div>", unsafe_allow_html=True)