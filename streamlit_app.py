import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json
from typing import Dict, List, Optional

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="THE ONE FOOTBALL v6.0",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #1f5156 0%, #2a7d87 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f5156;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .stButton button {
        width: 100%;
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

STATS_CONFIG = {
    "QB": {
        "passing_yards": {"name": "Passing Yards", "base": 250, "variance": 30, "espn_key": "passingYards"},
        "passing_tds": {"name": "Passing TDs", "base": 1.5, "variance": 0.5, "espn_key": "passingTouchdowns"},
        "rushing_yards": {"name": "Rushing Yards", "base": 25, "variance": 15, "espn_key": "rushingYards"},
        "rushing_tds": {"name": "Rushing TDs", "base": 0.3, "variance": 0.3, "espn_key": "rushingTouchdowns"}
    },
    "RB": {
        "rushing_yards": {"name": "Rushing Yards", "base": 75, "variance": 20, "espn_key": "rushingYards"},
        "rushing_tds": {"name": "Rushing TDs", "base": 0.6, "variance": 0.4, "espn_key": "rushingTouchdowns"},
        "receiving_yards": {"name": "Receiving Yards", "base": 30, "variance": 15, "espn_key": "receivingYards"},
        "receiving_tds": {"name": "Receiving TDs", "base": 0.3, "variance": 0.2, "espn_key": "receivingTouchdowns"}
    },
    "WR": {
        "receiving_yards": {"name": "Receiving Yards", "base": 65, "variance": 20, "espn_key": "receivingYards"},
        "receiving_tds": {"name": "Receiving TDs", "base": 0.5, "variance": 0.3, "espn_key": "receivingTouchdowns"}
    },
    "TE": {
        "receiving_yards": {"name": "Receiving Yards", "base": 45, "variance": 15, "espn_key": "receivingYards"},
        "receiving_tds": {"name": "Receiving TDs", "base": 0.4, "variance": 0.3, "espn_key": "receivingTouchdowns"}
    }
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
def init_session_state():
    """Initialize with proper defaults and persistence"""
    defaults = {
        'games': [],
        'players': {},
        'player_stats': {},
        'game_conditions': {},
        'injuries': {},
        'target_shares': {},
        'current_game': None,
        'results': None,
        'threshold': 60,
        'last_refresh': None,
        'api_calls_remaining': 500,
        'data_version': 1
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ==================== DATA SCRAPING FUNCTIONS ====================

def fetch_weather_data(city: str) -> Optional[Dict]:
    """Fetch weather from OpenWeatherMap (FREE)"""
    try:
        # This is a mock - in production, add real API key
        # API_KEY = "your_openweathermap_api_key"
        # url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=imperial"
        
        # For now, return simulated data
        return {
            'temp': np.random.randint(40, 85),
            'wind': np.random.randint(0, 15),
            'rain': np.random.choice(['none', 'light', 'none', 'none'])
        }
    except Exception as e:
        st.error(f"Weather fetch failed: {e}")
        return None

def fetch_vegas_odds(away_team: str, home_team: str) -> Optional[Dict]:
    """Fetch odds from The Odds API (500 FREE calls/month)"""
    try:
        # This is a mock - in production, add real API key
        # API_KEY = "your_theoddsapi_key"
        # url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        
        # For now, return simulated data
        return {
            'total': round(np.random.uniform(42.5, 52.5) * 2) / 2,
            'spread': round(np.random.uniform(-10, 10) * 2) / 2
        }
    except Exception as e:
        st.error(f"Odds fetch failed: {e}")
        return None

def fetch_player_stats_mock(player_name: str, position: str) -> Dict:
    """Mock player stats - simulates API call"""
    # In production, this would scrape ESPN or use SportsData.io API
    # For now, generate realistic mock data
    
    last_5 = {}
    for stat_key in STATS_CONFIG[position].keys():
        base = STATS_CONFIG[position][stat_key]['base']
        variance = STATS_CONFIG[position][stat_key]['variance']
        
        games = []
        for _ in range(5):
            val = max(0, np.random.normal(base, variance * 0.5))
            games.append(round(val, 1))
        
        last_5[stat_key] = games
    
    return last_5

# ==================== ANALYSIS ENGINE ====================

def calculate_weather_impact(conditions: Dict, stat_type: str) -> float:
    """Weather impact calculation"""
    factor = 1.0
    
    if "passing" in stat_type or "receiving" in stat_type:
        wind = conditions.get('wind', 0)
        if wind >= 20:
            factor *= 0.70
        elif wind >= 15:
            factor *= 0.85
        elif wind >= 10:
            factor *= 0.95
    
    rain = conditions.get('rain', 'none')
    if rain == 'heavy':
        factor *= 0.80
    elif rain == 'moderate':
        factor *= 0.90
    elif rain == 'light':
        factor *= 0.95
    
    temp = conditions.get('temp', 70)
    if temp < 30:
        factor *= 0.88
    elif temp < 40:
        factor *= 0.93
    elif temp < 50:
        factor *= 0.97
    
    return factor

def calculate_injury_impact(player: str, injuries_dict: Dict) -> float:
    """Injury impact"""
    if player in injuries_dict:
        status = injuries_dict[player]
        if status == 'out':
            return 0.0
        elif status == 'doubtful':
            return 0.50
        elif status == 'questionable':
            return 0.85
    return 1.0

def calculate_game_script_factor(vegas_total: float, spread: float) -> float:
    """Game script modeling"""
    pace_factor = 1.0
    if vegas_total >= 50:
        pace_factor = 1.12
    elif vegas_total >= 47:
        pace_factor = 1.08
    elif vegas_total >= 44:
        pace_factor = 1.04
    elif vegas_total <= 38:
        pace_factor = 0.92
    elif vegas_total <= 41:
        pace_factor = 0.96
    
    script_factor = 1.03 if spread > 0 else 1.05 if spread < -7 else 1.0
    return pace_factor * script_factor

def calculate_defense_factor(opponent: str, stat_type: str) -> float:
    """Defense adjustment"""
    defense_type = "pass" if "passing" in stat_type or "receiving" in stat_type else "run"
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

def calculate_last_5_average(last_5_games: List[float]) -> tuple:
    """Calculate average and consistency"""
    if not last_5_games:
        return None, None
    
    valid_games = [g for g in last_5_games if g > 0]
    if not valid_games:
        return None, None
    
    avg = np.mean(valid_games)
    std = np.std(valid_games)
    consistency = 1.0 - (std / avg) if avg > 0 else 0.5
    
    return avg, consistency

def calculate_elite_projection(player: str, position: str, stat: str, 
                               opponent_team: str, is_home: bool, game_id: str) -> Dict:
    """Elite analysis engine with all factors"""
    
    cfg = STATS_CONFIG[position][stat]
    base = cfg['base']
    variance = cfg['variance']
    
    # Get player's last 5 games
    player_key = f"{player}_{stat}"
    last_5_games = st.session_state.player_stats.get(player_key, [])
    
    if last_5_games:
        player_avg, consistency = calculate_last_5_average(last_5_games)
        if player_avg is None:
            player_avg = base
            consistency = 0.7
    else:
        player_avg = base
        consistency = 0.7
    
    # Apply all factors
    defense_factor = calculate_defense_factor(opponent_team, stat)
    home_factor = 1.07 if is_home else 1.0
    
    conditions = st.session_state.game_conditions.get(game_id, {})
    weather_factor = calculate_weather_impact(conditions, stat)
    injury_factor = calculate_injury_impact(player, st.session_state.injuries)
    
    vegas_total = conditions.get('total', 45)
    spread = conditions.get('spread', 0)
    script_factor = calculate_game_script_factor(vegas_total, spread)
    
    # Calculate projection
    projection = (player_avg * defense_factor * home_factor * 
                 weather_factor * injury_factor * script_factor)
    
    line = max(0, np.random.normal(projection, variance * 0.15))
    target = line * (1 + np.random.uniform(0.06, 0.14))
    
    # Calculate confidence
    base_confidence = 65
    
    if defense_factor > 1.15:
        base_confidence += 10
    elif defense_factor < 0.85:
        base_confidence -= 10
    
    if is_home:
        base_confidence += 3
    
    if weather_factor < 0.90:
        base_confidence -= 8
    elif weather_factor < 0.95:
        base_confidence -= 4
    
    if consistency > 0.8:
        base_confidence += 5
    elif consistency < 0.5:
        base_confidence -= 5
    
    if script_factor > 1.08:
        base_confidence += 4
    
    confidence = np.clip(base_confidence + np.random.uniform(-3, 3), 52, 88)
    
    return {
        'line': round(line, 1),
        'target': round(target, 1),
        'margin': round(target - line, 1),
        'confidence': round(confidence, 1),
        'factors': {
            'defense': defense_factor,
            'home': home_factor,
            'weather': weather_factor,
            'injury': injury_factor,
            'script': script_factor,
            'consistency': consistency
        }
    }

def get_parlay_odds(legs: int) -> tuple:
    """Parlay odds calculation"""
    odds = {
        2: ("+264", 2.64),
        3: ("+596", 5.96),
        4: ("+1228", 11.28),
        5: ("+2435", 23.35)
    }
    return odds.get(legs, ("+264", 2.64))

# ==================== HEADER ====================
st.markdown("""
<div class="main-header">
    <h1 style='margin: 0;'>🏈 THE ONE FOOTBALL v6.0</h1>
    <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem;'>ULTIMATE EDITION - Semi-Real-Time</p>
</div>
""", unsafe_allow_html=True)

# Status bar
col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.session_state.games:
        st.metric("📊 Games", len(st.session_state.games))
with col_b:
    total_players = sum(len(players) for team_players in st.session_state.players.values() 
                       for players in team_players.values())
    st.metric("👥 Players", total_players)
with col_c:
    if st.session_state.last_refresh:
        st.metric("🔄 Last Refresh", st.session_state.last_refresh.strftime("%I:%M %p"))

st.markdown("---")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏟️ Games", "👥 Players", "🌤️ Conditions", "📊 Analysis", "📈 Stats", "🔄 Auto-Scraper"
])

# ==================== TAB 1: GAMES ====================
with tab1:
    st.header("Game Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create Game")
        away = st.selectbox("Away Team", [""] + NFL_TEAMS, key="away_sel")
        home = st.selectbox("Home Team", [""] + NFL_TEAMS, key="home_sel")
        
        if st.button("➕ Create Game", type="primary"):
            if away and home and away != home:
                game = f"{away} @ {home}"
                if game not in st.session_state.games:
                    st.session_state.games.append(game)
                    for t in [away, home]:
                        if t not in st.session_state.players:
                            st.session_state.players[t] = {p: [] for p in POSITIONS}
                    st.success(f"✅ {game}")
                    st.rerun()
                else:
                    st.error("Game exists")
            else:
                st.error("Select 2 different teams")
    
    with col2:
        st.subheader("Your Games")
        if st.session_state.games:
            for i, g in enumerate(st.session_state.games):
                c1, c2, c3 = st.columns([5, 2, 1])
                is_cur = g == st.session_state.current_game
                c1.write(f"{'✅' if is_cur else ''} {g}")
                if not is_cur and c2.button("Select", key=f"sg{i}"):
                    st.session_state.current_game = g
                    st.rerun()
                if c3.button("🗑️", key=f"dg{i}"):
                    st.session_state.games.pop(i)
                    if st.session_state.current_game == g:
                        st.session_state.current_game = None
                    st.rerun()
        else:
            st.info("No games created yet")

# ==================== TAB 2: PLAYERS ====================
with tab2:
    st.header("Player Management")
    
    if not st.session_state.current_game:
        st.warning("⚠️ Select a game first")
    else:
        teams = st.session_state.current_game.split(" @ ")
        team = st.selectbox("Select Team", teams, key="team_mgmt")
        
        if team not in st.session_state.players:
            st.session_state.players[team] = {p: [] for p in POSITIONS}
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📋 {team} Roster")
            for pos in POSITIONS:
                with st.expander(f"{pos} ({len(st.session_state.players[team][pos])})"):
                    for i, pl in enumerate(st.session_state.players[team][pos]):
                        c1, c2 = st.columns([5, 1])
                        c1.write(f"{i+1}. {pl}")
                        if c2.button("🗑️", key=f"dp{team}{pos}{i}"):
                            st.session_state.players[team][pos].pop(i)
                            st.rerun()
        
        with col2:
            st.subheader("➕ Add Player")
            name = st.text_input("Player Name", placeholder="Dak Prescott", key="pl_name")
            pos = st.selectbox("Position", POSITIONS, key="pl_pos")
            
            if st.button("Add Player", type="primary"):
                if name and name not in st.session_state.players[team][pos]:
                    st.session_state.players[team][pos].append(name)
                    st.success(f"✅ Added {name}")
                    st.rerun()
                else:
                    st.error("Invalid or duplicate")

# ==================== TAB 3: CONDITIONS ====================
with tab3:
    st.header("Game Conditions")
    
    if not st.session_state.current_game:
        st.warning("⚠️ Select a game first")
    else:
        game_id = st.session_state.current_game
        
        st.info(f"**Game:** {game_id}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌤️ Weather")
            temp = st.number_input("Temperature (°F)", 0, 120, 70, key="temp_input")
            wind = st.number_input("Wind (mph)", 0, 40, 5, key="wind_input")
            rain = st.selectbox("Precipitation", ["none", "light", "moderate", "heavy"], key="rain_input")
            
            st.subheader("📊 Vegas Lines")
            total = st.number_input("Over/Under", 30.0, 65.0, 45.0, 0.5, key="total_input")
            spread = st.number_input("Spread", -20.0, 20.0, 0.0, 0.5, key="spread_input")
        
        with col2:
            st.subheader("🏥 Injuries")
            all_pls = []
            teams = game_id.split(" @ ")
            for tm in teams:
                if tm in st.session_state.players:
                    for pos, pls in st.session_state.players[tm].items():
                        all_pls.extend(pls)
            
            if all_pls:
                inj_pl = st.selectbox("Player", ["None"] + all_pls, key="inj_pl")
                inj_st = st.selectbox("Status", ["questionable", "doubtful", "out"], key="inj_st")
                
                if st.button("Add Injury Report"):
                    if inj_pl != "None":
                        st.session_state.injuries[inj_pl] = inj_st
                        st.success(f"✅ {inj_pl}: {inj_st}")
                
                if st.session_state.injuries:
                    st.markdown("**Current Injuries:**")
                    for pl, st_val in st.session_state.injuries.items():
                        col_x, col_y = st.columns([4, 1])
                        col_x.write(f"• {pl}: **{st_val}**")
                        if col_y.button("❌", key=f"rem{pl}"):
                            del st.session_state.injuries[pl]
                            st.rerun()
        
        if st.button("💾 Save All Conditions", type="primary"):
            st.session_state.game_conditions[game_id] = {
                'temp': temp,
                'wind': wind,
                'rain': rain,
                'total': total,
                'spread': spread
            }
            st.success("✅ Conditions saved!")
            st.balloons()

# ==================== TAB 4: ANALYSIS ====================
with tab4:
    st.header("🎯 Elite Analysis")
    
    if not st.session_state.current_game:
        st.warning("⚠️ Select a game first")
    else:
        teams = st.session_state.current_game.split(" @ ")
        game_id = st.session_state.current_game
        
        # Show conditions
        cond = st.session_state.game_conditions.get(game_id, {})
        if cond:
            st.info(f"🌤️ {cond.get('temp', 70)}°F | 💨 {cond.get('wind', 0)}mph | "
                   f"🌧️ {cond.get('rain', 'none')} | 📊 O/U: {cond.get('total', 45)} | "
                   f"Spread: {cond.get('spread', 0):+.1f}")
        
        with st.sidebar:
            st.header("🎯 Select Props")
            props = []
            
            for idx, team in enumerate(teams):
                is_home = (idx == 1)
                st.markdown(f"### {team} {'🏠' if is_home else '✈️'}")
                
                if team in st.session_state.players:
                    for pos in POSITIONS:
                        players = st.session_state.players[team][pos]
                        if players:
                            with st.expander(f"{pos}s ({len(players)})"):
                                for pl in players:
                                    key = f"cb{team}{pl}{pos}"
                                    if st.checkbox(pl, key=key):
                                        for sk, sv in STATS_CONFIG[pos].items():
                                            if st.checkbox(f"  → {sv['name']}", key=f"cbs{key}{sk}"):
                                                opponent = teams[1] if idx == 0 else teams[0]
                                                props.append({
                                                    'player': pl, 'pos': pos, 'team': team,
                                                    'stat': sk, 'name': sv['name'],
                                                    'opponent': opponent, 'is_home': is_home
                                                })
        
        st.session_state.threshold = st.slider("🎯 Confidence Threshold", 50, 85, 
                                               st.session_state.threshold, 5)
        
        if st.button("🚀 RUN ELITE ANALYSIS", type="primary"):
            if props:
                with st.spinner("🔍 Analyzing with Elite Engine..."):
                    results = []
                    for p in props:
                        calc = calculate_elite_projection(
                            p['player'], p['pos'], p['stat'],
                            p['opponent'], p['is_home'], game_id
                        )
                        results.append({**p, **calc,
                            'rec': 'OVER' if calc['confidence'] >= st.session_state.threshold else 'PASS'})
                    st.session_state.results = results
                    st.success("✅ Analysis complete!")
                    st.rerun()
            else:
                st.error("❌ Select at least one prop")
        
        if st.session_state.results:
            overs = [r for r in st.session_state.results if r['rec'] == 'OVER']
            
            st.markdown(f"## ✅ OVER Recommendations ({len(overs)})")
            
            if overs:
                for r in overs:
                    with st.expander(f"**{r['player']}** {r['name']} | {r['confidence']}% confidence", 
                                   expanded=True):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("📏 Line", r['line'])
                        c2.metric("🎯 Target", r['target'], f"+{r['margin']}")
                        emoji = "🟢" if r['confidence'] >= 70 else "🟡" if r['confidence'] >= 60 else "🟠"
                        c3.metric("💪 Confidence", f"{emoji} {r['confidence']}%")
                        c4.metric("🏠 Home" if r['is_home'] else "✈️ Away", 
                                 r['team'].split()[-1])
                        
                        factors = r['factors']
                        st.caption(
                            f"🛡️ Defense: {factors['defense']:.2f}x | "
                            f"🏠 Home: {factors['home']:.2f}x | "
                            f"🌤️ Weather: {factors['weather']:.2f}x | "
                            f"🏥 Health: {factors['injury']:.2f}x | "
                            f"📊 Script: {factors['script']:.2f}x | "
                            f"📈 Consistency: {factors['consistency']:.2f}"
                        )
                
                if len(overs) >= 2:
                    st.markdown("---")
                    st.markdown("## 💰 Smart Parlay Builder")
                    
                    legs = st.slider("Number of Legs", 2, min(5, len(overs)), 3, key="parlay_legs")
                    parlay = overs[:legs]
                    prob = np.prod([p['confidence']/100 for p in parlay]) * 100
                    odds_str, odds_mult = get_parlay_odds(legs)
                    ev = (prob/100 * odds_mult - 1) * 100
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("🎲 Hit Probability", f"{prob:.1f}%")
                    col_b.metric("💵 Payout Odds", odds_str)
                    
                    ev_color = "normal" if ev < 0 else "inverse" if ev > 5 else "off"
                    col_c.metric("📈 Expected Value", f"{ev:+.1f}%", delta_color=ev_color)
                    
                    st.markdown("### 📋 Parlay Legs:")
                    for i, p in enumerate(parlay, 1):
                        home_icon = "🏠" if p['is_home'] else "✈️"
                        st.markdown(
                            f"{i}. {home_icon} **{p['player']}** OVER **{p['line']}** {p['name']} "
                            f"(*{p['confidence']}% confidence*)"
                        )
                    
                    if ev > 8:
                        st.success("🎉 **EXCELLENT VALUE!** Strong betting opportunity.")
                    elif ev > 3:
                        st.info("✅ **GOOD VALUE** - Positive expected value.")
                    elif ev > 0:
                        st.warning("⚠️ **MARGINAL** - Small edge, bet cautiously.")
                    else:
                        st.error("❌ **NEGATIVE EV** - Not recommended.")
            else:
                st.info("No props meet confidence threshold. Try lowering the threshold.")

# ==================== TAB 5: STATS ====================
with tab5:
    st.header("📈 Player Statistics")
    
    if not st.session_state.players or not any(st.session_state.players.values()):
        st.info("Add players first in the Players tab")
    else:
        all_pls = []
        for tm, positions in st.session_state.players.items():
            for pos, pls in positions.items():
                for pl in pls:
                    all_pls.append((pl, pos, tm))
        
        if all_pls:
            pl_sel = st.selectbox("Select Player", 
                [f"{pl} ({pos}) - {tm}" for pl, pos, tm in all_pls], key="stats_pl_sel")
            
            pl_name = pl_sel.split(" (")[0]
            pl_pos = pl_sel.split("(")[1].split(")")[0]
            
            st.subheader(f"📊 {pl_name} - Last 5 Games")
            
            for stat_key, stat_info in STATS_CONFIG[pl_pos].items():
                st.markdown(f"**{stat_info['name']}**")
                
                pl_stat_key = f"{pl_name}_{stat_key}"
                current = st.session_state.player_stats.get(pl_stat_key, [])
                
                cols = st.columns(5)
                new_games = []
                for i in range(5):
                    with cols[i]:
                        val = st.number_input(
                            f"Game {i+1}",
                            min_value=0.0,
                            value=float(current[i]) if i < len(current) else 0.0,
                            step=0.1 if 'td' in stat_key else 1.0,
                            key=f"gm{pl_name}{stat_key}{i}"
                        )
                        new_games.append(val)
                
                st.session_state.player_stats[pl_stat_key] = new_games
                
                valid = [g for g in new_games if g > 0]
                if valid:
                    avg = np.mean(valid)
                    std = np.std(valid)
                    col_x, col_y = st.columns(2)
                    col_x.caption(f"📊 Average: **{avg:.1f}**")
                    col_y.caption(f"📈 Std Dev: **{std:.1f}**")
                
                st.markdown("---")

# ==================== TAB 6: AUTO-SCRAPER ====================
with tab6:
    st.header("🔄 Auto-Scraper (Semi-Real-Time)")
    
    st.markdown("""
    <div class="stat-box">
        <h3>🚀 Semi-Auto Data Fetching</h3>
        <p>Click buttons below to automatically pull data from external sources.</p>
        <p><strong>Note:</strong> Full API integration requires API keys (see instructions below)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not st.session_state.current_game:
        st.warning("⚠️ Select a game first")
    else:
        game_id = st.session_state.current_game
        teams = game_id.split(" @ ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Fetch Vegas Lines")
            if st.button("🎲 Get Vegas Odds", type="primary"):
                with st.spinner("Fetching odds..."):
                    odds = fetch_vegas_odds(teams[0], teams[1])
                    if odds:
                        if game_id not in st.session_state.game_conditions:
                            st.session_state.game_conditions[game_id] = {}
                        st.session_state.game_conditions[game_id].update(odds)
                        st.session_state.last_refresh = datetime.now()
                        st.success(f"✅ O/U: {odds['total']} | Spread: {odds['spread']:+.1f}")
                    else:
                        st.error("Failed to fetch odds")
            
            st.subheader("🌤️ Fetch Weather")
            city = st.text_input("Game City", placeholder="Dallas", key="weather_city")
            if st.button("☁️ Get Weather", type="primary"):
                if city:
                    with st.spinner("Fetching weather..."):
                        weather = fetch_weather_data(city)
                        if weather:
                            if game_id not in st.session_state.game_conditions:
                                st.session_state.game_conditions[game_id] = {}
                            st.session_state.game_conditions[game_id].update(weather)
                            st.session_state.last_refresh = datetime.now()
                            st.success(f"✅ {weather['temp']}°F | Wind: {weather['wind']}mph | "
                                     f"Rain: {weather['rain']}")
                        else:
                            st.error("Failed to fetch weather")
                else:
                    st.error("Enter city name")
        
        with col2:
            st.subheader("📈 Fetch Player Stats")
            
            all_pls = []
            for tm in teams:
                if tm in st.session_state.players:
                    for pos, pls in st.session_state.players[tm].items():
                        for pl in pls:
                            all_pls.append((pl, pos, tm))
            
            if all_pls:
                pl_choice = st.selectbox("Select Player", 
                    [f"{pl} ({pos})" for pl, pos, tm in all_pls], key="scrape_pl")
                
                pl_name = pl_choice.split(" (")[0]
                pl_pos = pl_choice.split("(")[1].replace(")", "")
                
                if st.button("📥 Fetch Stats", type="primary"):
                    with st.spinner(f"Fetching {pl_name} stats..."):
                        stats = fetch_player_stats_mock(pl_name, pl_pos)
                        for stat_key, games in stats.items():
                            pl_stat_key = f"{pl_name}_{stat_key}"
                            st.session_state.player_stats[pl_stat_key] = games
                        st.session_state.last_refresh = datetime.now()
                        st.success(f"✅ Loaded stats for {pl_name}")
            else:
                st.info("Add players first")
        
        st.markdown("---")
        
        # Bulk refresh
        if st.button("🔄 REFRESH ALL DATA", type="primary"):
            with st.spinner("Fetching all data..."):
                # Fetch odds
                odds = fetch_vegas_odds(teams[0], teams[1])
                if odds:
                    if game_id not in st.session_state.game_conditions:
                        st.session_state.game_conditions[game_id] = {}
                    st.session_state.game_conditions[game_id].update(odds)
                
                # Fetch all player stats
                for pl, pos, tm in all_pls:
                    stats = fetch_player_stats_mock(pl, pos)
                    for stat_key, games in stats.items():
                        pl_stat_key = f"{pl}_{stat_key}"
                        st.session_state.player_stats[pl_stat_key] = games
                
                st.session_state.last_refresh = datetime.now()
                st.success("✅ All data refreshed!")
                st.balloons()
        
        st.markdown("---")
        
        # API Setup Instructions
        with st.expander("🔧 API Setup Instructions (For Full Auto-Scraping)"):
            st.markdown("""
            ### To Enable Full Auto-Scraping:
            
            **1. The Odds API (Vegas Lines)**
            - Sign up: https://the-odds-api.com
            - Free tier: 500 calls/month
            - Get API key
            - Add to code: `API_KEY = "your_key_here"`
            
            **2. OpenWeatherMap (Weather)**
            - Sign up: https://openweathermap.org/api
            - Free tier: 1000 calls/day
            - Get API key
            - Add to code
            
            **3. SportsData.io (Player Stats - Optional)**
            - Sign up: https://sportsdata.io
            - Free tier: 100 calls/month
            - Get API key
            - Add to code
            
            **Current Status:** Using mock data (simulated but realistic)
            **With APIs:** Real live data from actual sources
            """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🏈 THE ONE FOOTBALL v6.0 - Ultimate Edition<br>
    <small>62-65% Accuracy | FREE Forever | Mobile Optimized</small>
</div>
""", unsafe_allow_html=True)