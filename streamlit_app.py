import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="THE ONE FOOTBALL v8.0 FINAL",
    page_icon="🏈",
    layout="wide"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CONSTANTS ====================
NFL_TEAMS = sorted([
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
])

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
    "Arizona Cardinals": {"pass": 28, "run": 22},
    "Atlanta Falcons": {"pass": 24, "run": 20},
    "Baltimore Ravens": {"pass": 8, "run": 5},
    "Buffalo Bills": {"pass": 12, "run": 10},
    "Carolina Panthers": {"pass": 25, "run": 26},
    "Chicago Bears": {"pass": 15, "run": 14},
    "Cincinnati Bengals": {"pass": 18, "run": 21},
    "Cleveland Browns": {"pass": 10, "run": 8},
    "Dallas Cowboys": {"pass": 11, "run": 16},
    "Denver Broncos": {"pass": 14, "run": 13},
    "Detroit Lions": {"pass": 22, "run": 18},
    "Green Bay Packers": {"pass": 16, "run": 17},
    "Houston Texans": {"pass": 20, "run": 19},
    "Indianapolis Colts": {"pass": 23, "run": 24},
    "Jacksonville Jaguars": {"pass": 26, "run": 27},
    "Kansas City Chiefs": {"pass": 13, "run": 12},
    "Las Vegas Raiders": {"pass": 27, "run": 25},
    "Los Angeles Chargers": {"pass": 17, "run": 15},
    "Los Angeles Rams": {"pass": 19, "run": 23},
    "Miami Dolphins": {"pass": 21, "run": 28},
    "Minnesota Vikings": {"pass": 9, "run": 11},
    "New England Patriots": {"pass": 7, "run": 9},
    "New Orleans Saints": {"pass": 6, "run": 7},
    "New York Giants": {"pass": 29, "run": 29},
    "New York Jets": {"pass": 5, "run": 6},
    "Philadelphia Eagles": {"pass": 4, "run": 3},
    "Pittsburgh Steelers": {"pass": 3, "run": 4},
    "San Francisco 49ers": {"pass": 2, "run": 2},
    "Seattle Seahawks": {"pass": 30, "run": 30},
    "Tampa Bay Buccaneers": {"pass": 31, "run": 31},
    "Tennessee Titans": {"pass": 32, "run": 32},
    "Washington Commanders": {"pass": 1, "run": 1}
}

# Popular players for quick-add
POPULAR_PLAYERS = {
    "QB": ["Dak Prescott", "Kyler Murray", "Patrick Mahomes", "Josh Allen", "Lamar Jackson"],
    "RB": ["Javonte Williams", "Bam Knight", "Saquon Barkley", "Christian McCaffrey"],
    "WR": ["CeeDee Lamb", "Marvin Harrison Jr.", "Tyreek Hill", "Justin Jefferson", "George Pickens"],
    "TE": ["Jake Ferguson", "Trey McBride", "Travis Kelce", "George Kittle"]
}

# ==================== SESSION STATE ====================
def init_session_state():
    defaults = {
        'games': [],
        'players': {},
        'game_conditions': {},
        'current_game': None,
        'analysis_results': [],
        'parlay_history': [],
        'app_version': '8.0'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ==================== CORE FUNCTIONS ====================

def calculate_defense_factor(opponent, stat_type):
    """Calculate defensive impact multiplier"""
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
    """Elite projection engine with all factors"""
    cfg = STATS_CONFIG[stat]
    base = cfg['base']
    variance = cfg['variance']
    
    # Position-specific base adjustments
    adjustments = {
        ("QB", "rushing_yards"): 25,
        ("QB", "rushing_tds"): 0.3,
        ("RB", "rushing_yards"): 75,
        ("RB", "receiving_yards"): 30,
        ("WR", "receiving_yards"): 65,
        ("WR", "receptions"): 6.0,
        ("TE", "receiving_yards"): 45,
        ("TE", "receptions"): 5.0
    }
    
    base = adjustments.get((position, stat), base)
    
    # Calculate all factors
    defense_factor = calculate_defense_factor(opponent, stat)
    home_factor = 1.07 if is_home else 1.0
    
    conditions = st.session_state.game_conditions.get(game_id, {})
    total = conditions.get('total', 45)
    spread = conditions.get('spread', 0)
    
    # Game script
    if total >= 50:
        script_factor = 1.12
    elif total >= 47:
        script_factor = 1.08
    elif total >= 44:
        script_factor = 1.04
    else:
        script_factor = 1.0
    
    # Calculate projection
    projection = base * defense_factor * home_factor * script_factor
    line = max(0, np.random.normal(projection, variance * 0.15))
    target = line * (1 + np.random.uniform(0.06, 0.14))
    
    # Confidence
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
        'player': player,
        'position': position,
        'stat': STATS_CONFIG[stat]['name'],
        'stat_key': stat,
        'line': round(line, 1),
        'target': round(target, 1),
        'margin': round(target - line, 1),
        'confidence': round(confidence, 1),
        'opponent': opponent,
        'is_home': is_home,
        'defense_factor': round(defense_factor, 2),
        'script_factor': round(script_factor, 2),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_parlay_odds(legs):
    """Get parlay payout odds"""
    odds_map = {
        2: ("+264", 2.64), 3: ("+596", 5.96), 4: ("+1228", 11.28),
        5: ("+2435", 23.35), 6: ("+4700", 47.0), 7: ("+7500", 75.0),
        8: ("+9500", 95.0), 9: ("+15000", 150.0), 10: ("+25000", 250.0),
        11: ("+35000", 350.0), 12: ("+40000", 400.0)
    }
    return odds_map.get(legs, ("+40000", 400.0))

def save_parlay(parlay_props, legs, prob, odds_str):
    """Save parlay to history"""
    parlay_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'game': st.session_state.current_game,
        'legs': legs,
        'probability': prob,
        'odds': odds_str,
        'props': parlay_props
    }
    st.session_state.parlay_history.append(parlay_data)

def export_parlay_text(parlay_props):
    """Generate copy-paste parlay text"""
    lines = []
    for i, p in enumerate(parlay_props, 1):
        home_icon = "HOME" if p['is_home'] else "AWAY"
        lines.append(f"{i}. {p['player']} ({home_icon}) OVER {p['line']} {p['stat']}")
    return "
".join(lines)

# ==================== HEADER ====================
st.markdown("""
<div style='text-align: center; background: linear-gradient(135deg, #1f5156 0%, #2a7d87 100%); 
     color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
    <h1 style='margin: 0;'>🏈 THE ONE FOOTBALL v8.0</h1>
    <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem;'>⚡ FINAL EDITION - Built to Win 💰</p>
</div>
""", unsafe_allow_html=True)

# Quick stats bar
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("📊 Games", len(st.session_state.games))
col_s2.metric("👥 Total Props", len(st.session_state.analysis_results))
col_s3.metric("📜 Parlays Saved", len(st.session_state.parlay_history))
col_s4.metric("🎯 Version", "8.0 FINAL")

# ==================== TABS ====================
tab1, tab2, tab3, tab4 = st.tabs(["🏟️ Setup", "👥 Players", "📊 Results", "📜 History"])

# ==================== TAB 1: SETUP ====================
with tab1:
    st.header("⚡ Game Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Create Game")
        away = st.selectbox("Away Team", [""] + NFL_TEAMS, key="away")
        home = st.selectbox("Home Team", [""] + NFL_TEAMS, key="home")
        
        if st.button("➕ Create Game", type="primary"):
            if away and home and away != home:
                game = f"{away} @ {home}"
                if game not in st.session_state.games:
                    st.session_state.games.append(game)
                    st.session_state.players[game] = []
                    st.success(f"✅ {game}")
                    st.balloons()
                    st.rerun()
    
    with col2:
        st.subheader("2️⃣ Game Conditions")
        if st.session_state.games:
            sel_game = st.selectbox("Select Game", st.session_state.games)
            total = st.number_input("Over/Under", 30.0, 65.0, 48.5, 0.5)
            spread = st.number_input("Spread", -20.0, 20.0, -7.5, 0.5)
            
            if st.button("💾 Activate", type="primary"):
                st.session_state.game_conditions[sel_game] = {'total': total, 'spread': spread}
                st.session_state.current_game = sel_game
                st.success(f"✅ Active: {sel_game}")
                st.rerun()
    
    if st.session_state.current_game:
        st.markdown("---")
        st.success(f"**🎯 ACTIVE:** {st.session_state.current_game}")
        cond = st.session_state.game_conditions.get(st.session_state.current_game, {})
        if cond:
            st.info(f"📊 O/U: {cond['total']} | Spread: {con