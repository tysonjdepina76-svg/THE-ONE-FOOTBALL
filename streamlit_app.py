import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="THE ONE FOOTBALL v7.0",
    page_icon="🏈",
    layout="wide"
)

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

# Auto stats by position
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

# ==================== SESSION STATE ====================
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

# ==================== FUNCTIONS ====================

def calculate_defense_factor(opponent, stat_type):
    defense_type = "pass" if "passing" in stat_type or "receiving" in stat_type or "receptions" in stat_type else "run"
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
    
    # Adjust base by position
    if position == "QB" and stat == "rushing_yards":
        base = 25
    elif position == "QB" and stat == "rushing_tds":
        base = 0.3
    elif position == "RB" and stat == "rushing_yards":
        base = 75
    elif position == "RB" and stat == "receiving_yards":
        base = 30
    elif position == "WR" and stat == "receiving_yards":
        base = 65
    elif position == "TE" and stat == "receiving_yards":
        base = 45
    
    defense_factor = calculate_defense_factor(opponent, stat)
    home_factor = 1.07 if is_home else 1.0
    
    conditions = st.session_state.game_conditions.get(game_id, {})
    total = conditions.get('total', 45)
    spread = conditions.get('spread', 0)
    
    # Game script
    script_factor = 1.08 if total >= 47 else 1.04 if total >= 44 else 1.0
    
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
    
    confidence = np.clip(base_confidence + np.random.uniform(-3, 3), 55, 85)
    
    return {
        'player': player,
        'position': position,
        'stat': STATS_CONFIG[stat]['name'],
        'line': round(line, 1),
        'target': round(target, 1),
        'margin': round(target - line, 1),
        'confidence': round(confidence, 1),
        'opponent': opponent,
        'is_home': is_home
    }

# ==================== HEADER ====================
st.markdown("""
<div style='text-align: center; background: linear-gradient(135deg, #1f5156 0%, #2a7d87 100%); 
     color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
    <h1 style='margin: 0;'>🏈 THE ONE FOOTBALL v7.0</h1>
    <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem;'>ONE-CLICK ANALYSIS - No Manual Prop Selection!</p>
</div>
""", unsafe_allow_html=True)

# ==================== TABS ====================
tab1, tab2, tab3 = st.tabs(["🏟️ Setup Game", "👥 Add Players & Analyze", "📊 Results"])

# ==================== TAB 1: SETUP ====================
with tab1:
    st.header("⚡ Quick Game Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create Game")
        away = st.selectbox("Away Team", [""] + NFL_TEAMS, key="away")
        home = st.selectbox("Home Team", [""] + NFL_TEAMS, key="home")
        
        if st.button("➕ Create Game", type="primary"):
            if away and home and away != home:
                game = f"{away} @ {home}"
                if game not in st.session_state.games:
                    st.session_state.games.append(game)
                    st.session_state.players[game] = []
                    st.success(f"✅ {game}")
                    st.rerun()
    
    with col2:
        st.subheader("Set Conditions")
        if st.session_state.games:
            sel_game = st.selectbox("Select Game", st.session_state.games, key="cond_game")
            
            total = st.number_input("Over/Under", 30.0, 65.0, 45.0, 0.5)
            spread = st.number_input("Spread", -20.0, 20.0, 0.0, 0.5)
            
            if st.button("💾 Save Conditions"):
                st.session_state.game_conditions[sel_game] = {'total': total, 'spread': spread}
                st.session_state.current_game = sel_game
                st.success("✅ Saved!")
                st.rerun()

# ==================== TAB 2: ADD PLAYERS ====================
with tab2:
    st.header("👥 Add Players & Auto-Analyze")
    
    if not st.session_state.current_game:
        st.warning("⚠️ Create a game and set conditions first (Tab 1)")
    else:
        st.info(f"**Current Game:** {st.session_state.current_game}")
        
        teams = st.session_state.current_game.split(" @ ")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("➕ Add Player")
            
            team = st.selectbox("Team", teams, key="add_team")
            name = st.text_input("Player Name", placeholder="Dak Prescott")
            pos = st.selectbox("Position", POSITIONS)
            
            if st.button("➕ Add & Auto-Analyze", type="primary"):
                if name:
                    player_data = {
                        'name': name,
                        'position': pos,
                        'team': team
                    }
                    
                    if st.session_state.current_game not in st.session_state.players:
                        st.session_state.players[st.session_state.current_game] = []
                    
                    st.session_state.players[st.session_state.current_game].append(player_data)
                    
                    # AUTO-ANALYZE
                    is_home = (team == teams[1])
                    opponent = teams[1] if team == teams[0] else teams[0]
                    
                    # Get all stats for position
                    stats = POSITION_STATS[pos]
                    
                    for stat in stats:
                        result = calculate_projection(
                            name, pos, stat, opponent, is_home, st.session_state.current_game
                        )
                        st.session_state.analysis_results.append(result)
                    
                    st.success(f"✅ Added {name} & analyzed {len(stats)} props!")
                    st.rerun()
        
        with col2:
            st.subheader("📋 Current Players")
            if st.session_state.current_game in st.session_state.players:
                players = st.session_state.players[st.session_state.current_game]
                if players:
                    for i, p in enumerate(players):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        c1.write(f"{p['name']}")
                        c2.write(f"{p['position']} - {p['team']}")
                        if c3.button("🗑️", key=f"del{i}"):
                            players.pop(i)
                            # Remove from results
                            st.session_state.analysis_results = [
                                r for r in st.session_state.analysis_results 
                                if r['player'] != p['name']
                            ]
                            st.rerun()
                else:
                    st.info("No players added yet")

# ==================== TAB 3: RESULTS ====================
with tab3:
    st.header("📊 Analysis Results")
    
    if not st.session_state.analysis_results:
        st.info("No analysis yet. Add players in Tab 2!")
    else:
        # Filter by confidence
        threshold = st.slider("Min Confidence %", 50, 85, 60)
        
        filtered = [r for r in st.session_state.analysis_results if r['confidence'] >= threshold]
        
        st.markdown(f"### ✅ {len(filtered)} Props Over {threshold}% Confidence")
        
        if filtered:
            for r in filtered:
                with st.expander(f"**{r['player']}** - {r['stat']} | {r['confidence']}% 🎯"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Line", r['line'])
                    c2.metric("Target", r['target'], f"+{r['margin']}")
                    c3.metric("Confidence", f"{r['confidence']}%")
                    c4.metric("vs", r['opponent'])
            
            # Parlay builder
            if len(filtered) >= 2:
                st.markdown("---")
                st.markdown("### 💰 Build Parlay")
                
                legs = st.slider("Number of Legs", 2, min(12, len(filtered)), min(6, len(filtered)))
                parlay = filtered[:legs]
                
                prob = np.prod([p['confidence']/100 for p in parlay]) * 100
                
                # Odds calculation
                if legs == 2:
                    odds_str, mult = "+264", 2.64
                elif legs == 3:
                    odds_str, mult = "+596", 5.96
                elif legs == 4:
                    odds_str, mult = "+1228", 11.28
                elif legs == 5:
                    odds_str, mult = "+2435", 23.35
                elif legs == 6:
                    odds_str, mult = "+4700", 47.0
                elif legs == 8:
                    odds_str, mult = "+9500", 95.0
                elif legs == 10:
                    odds_str, mult = "+25000", 250.0
                else:
                    odds_str, mult = "+40000", 400.0
                
                ev = (prob/100 * mult - 1) * 100
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("🎲 Probability", f"{prob:.2f}%")
                col_b.metric("💵 Payout", odds_str)
                col_c.metric("📈 Expected Value", f"{ev:+.0f}%")
                
                st.markdown("**Parlay Legs:**")
                for i, p in enumerate(parlay, 1):
                    home_icon = "🏠" if p['is_home'] else "✈️"
                    st.markdown(f"{i}. {home_icon} **{p['player']}** OVER **{p['line']}** {p['stat']}")
                
                # Copy to clipboard format
                st.markdown("---")
                st.markdown("**📋 Copy This to Sportsbook:**")
                parlay_text = "
".join([
                    f"{i}. {p['player']} OVER {p['line']} {p['stat']}"
                    for i, p in enumerate(parlay, 1)
                ])
                st.code(parlay_text, language="text")
        else:
            st.info(f"No props meet {threshold}% threshold. Try lowering it.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>🏈 THE ONE FOOTBALL v7.0 - One-Click Edition</div>", unsafe_allow_html=True)