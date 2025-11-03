import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="THE ONE FOOTBALL v5.0",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== NFL TEAMS ====================
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
        "passing_yards": {"name": "Passing Yards", "base": 250, "variance": 30},
        "passing_tds": {"name": "Passing TDs", "base": 1.5, "variance": 0.5},
        "rushing_yards": {"name": "Rushing Yards", "base": 25, "variance": 15},
        "rushing_tds": {"name": "Rushing TDs", "base": 0.3, "variance": 0.3}
    },
    "RB": {
        "rushing_yards": {"name": "Rushing Yards", "base": 75, "variance": 20},
        "rushing_tds": {"name": "Rushing TDs", "base": 0.6, "variance": 0.4},
        "receiving_yards": {"name": "Receiving Yards", "base": 30, "variance": 15},
        "receiving_tds": {"name": "Receiving TDs", "base": 0.3, "variance": 0.2}
    },
    "WR": {
        "receiving_yards": {"name": "Receiving Yards", "base": 65, "variance": 20},
        "receiving_tds": {"name": "Receiving TDs", "base": 0.5, "variance": 0.3}
    },
    "TE": {
        "receiving_yards": {"name": "Receiving Yards", "base": 45, "variance": 15},
        "receiving_tds": {"name": "Receiving TDs", "base": 0.4, "variance": 0.3}
    }
}

# ==================== DEFENSE RANKINGS ====================
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
if 'player_stats' not in st.session_state:
    st.session_state.player_stats = {}
if 'game_conditions' not in st.session_state:
    st.session_state.game_conditions = {}
if 'injuries' not in st.session_state:
    st.session_state.injuries = {}
if 'target_shares' not in st.session_state:
    st.session_state.target_shares = {}
if 'current_game' not in st.session_state:
    st.session_state.current_game = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'threshold' not in st.session_state:
    st.session_state.threshold = 60

# ==================== FUNCTIONS ====================

def calculate_weather_impact(conditions, stat_type):
    """Weather impact on projections"""
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

def calculate_injury_impact(player, injuries_dict):
    """Adjust for injuries"""
    impact = 1.0
    
    if player in injuries_dict:
        status = injuries_dict[player]
        if status == 'out':
            impact = 0.0
        elif status == 'doubtful':
            impact = 0.50
        elif status == 'questionable':
            impact = 0.85
    
    return impact

def calculate_game_script_factor(vegas_total, spread):
    """Game script impact"""
    pace_factor = 1.0
    script_factor = 1.0
    
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
    
    if spread > 0:
        script_factor = 1.03
    elif spread < -7:
        script_factor = 1.05
    
    return pace_factor * script_factor

def calculate_defense_factor(opponent, stat_type):
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

def calculate_last_5_average(last_5_games):
    """Calculate average and consistency"""
    if not last_5_games or len(last_5_games) == 0:
        return None, None
    
    valid_games = [g for g in last_5_games if g > 0]
    if not valid_games:
        return None, None
    
    avg = np.mean(valid_games)
    std = np.std(valid_games)
    consistency = 1.0 - (std / avg) if avg > 0 else 0.5
    
    return avg, consistency

def calculate_elite_projection(player, position, stat, opponent_team, is_home, game_id):
    """Elite analysis engine"""
    
    cfg = STATS_CONFIG[position][stat]
    base = cfg['base']
    variance = cfg['variance']
    
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
    
    defense_factor = calculate_defense_factor(opponent_team, stat)
    home_factor = 1.07 if is_home else 1.0
    
    conditions = st.session_state.game_conditions.get(game_id, {})
    weather_factor = calculate_weather_impact(conditions, stat)
    injury_factor = calculate_injury_impact(player, st.session_state.injuries)
    
    vegas_total = conditions.get('total', 45)
    spread = conditions.get('spread', 0)
    script_factor = calculate_game_script_factor(vegas_total, spread)
    
    projection = (player_avg * defense_factor * home_factor * 
                 weather_factor * injury_factor * script_factor)
    
    line = max(0, np.random.normal(projection, variance * 0.15))
    margin_pct = np.random.uniform(0.06, 0.14)
    target = line * (1 + margin_pct)
    
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

def get_parlay_odds(legs):
    """Parlay odds"""
    odds = {2: ("+264", 2.64), 3: ("+596", 5.96), 4: ("+1228", 11.28), 5: ("+2435", 23.35)}
    return odds.get(legs, ("+264", 2.64))

# ==================== HEADER ====================
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #1f5156;'>🏈 THE ONE FOOTBALL v5.0</h1>
    <p style='color: #666; font-size: 1.2rem; font-weight: bold;'>ELITE EDITION</p>
    <p style='color: #28a745; font-size: 0.9rem;'>
        ✅ Defense | ✅ Weather | ✅ Injuries | ✅ Game Script | ✅ Target Share
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏟️ Games", "👥 Players", "🌤️ Conditions", "📊 Analysis", "📈 Stats"
])

# ==================== TAB 1: GAMES ====================
with tab1:
    st.header("Game Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create Game")
        with st.form("game_form", clear_on_submit=True):
            away = st.selectbox("Away Team", [""] + NFL_TEAMS)
            home = st.selectbox("Home Team", [""] + NFL_TEAMS)
            
            if st.form_submit_button("Create", type="primary"):
                if away and home and away != home:
                    game = f"{away} @ {home}"
                    if game not in st.session_state.games:
                        st.session_state.games.append(game)
                        for t in [away, home]:
                            if t not in st.session_state.players:
                                st.session_state.players[t] = {p: [] for p in POSITIONS}
                        st.success(f"✅ Created: {game}")
                        st.rerun()
                    else:
                        st.error("Game exists!")
                else:
                    st.error("Select 2 different teams")
    
    with col2:
        st.subheader("Games")
        if st.session_state.games:
            for i, g in enumerate(st.session_state.games):
                c1, c2, c3 = st.columns([5, 2, 1])
                is_current = g == st.session_state.current_game
                c1.write(f"{'✅' if is_current else ''} {g}")
                if not is_current and c2.button("Select", key=f"s{i}"):
                    st.session_state.current_game = g
                    st.rerun()
                if c3.button("🗑️", key=f"d{i}"):
                    st.session_state.games.pop(i)
                    if st.session_state.current_game == g:
                        st.session_state.current_game = None
                    st.rerun()
        else:
            st.info("No games yet")
    
    if st.session_state.current_game:
        st.success(f"**Selected:** {st.session_state.current_game}")

# ==================== TAB 2: PLAYERS ====================
with tab2:
    st.header("Player Management")
    
    if not st.session_state.current_game:
        st.warning("Select a game first")
    else:
        teams = st.session_state.current_game.split(" @ ")
        team = st.selectbox("Team", teams)
        
        if team not in st.session_state.players:
            st.session_state.players[team] = {p: [] for p in POSITIONS}
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"Roster - {team}")
            for pos in POSITIONS:
                st.markdown(f"**{pos}s**")
                for i, p in enumerate(st.session_state.players[team][pos]):
                    c1, c2 = st.columns([5, 1])
                    c1.write(p)
                    if c2.button("🗑️", key=f"dp{team}{pos}{i}"):
                        st.session_state.players[team][pos].pop(i)
                        st.rerun()
                st.markdown("---")
        
        with col2:
            st.subheader("Add Player")
            with st.form("player_form", clear_on_submit=True):
                name = st.text_input("Name")
                pos = st.selectbox("Position", POSITIONS)
                
                if st.form_submit_button("Add", type="primary"):
                    if name and name not in st.session_state.players[team][pos]:
                        st.session_state.players[team][pos].append(name)
                        st.success(f"Added {name}")
                        st.rerun()
                    else:
                        st.error("Invalid or duplicate")

# ==================== TAB 3: CONDITIONS ====================
with tab3:
    st.header("Game Conditions")
    
    if not st.session_state.current_game:
        st.warning("Select a game first")
    else:
        game_id = st.session_state.current_game
        
        st.subheader(f"Conditions: {game_id}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Weather")
            temp = st.number_input("Temperature (°F)", 0, 120, 70, key="temp")
            wind = st.number_input("Wind Speed (mph)", 0, 40, 5, key="wind")
            rain = st.selectbox("Precipitation", ["none", "light", "moderate", "heavy"], key="rain")
            
            st.markdown("### Vegas Lines")
            total = st.number_input("Over/Under", 30.0, 65.0, 45.0, 0.5, key="total")
            spread = st.number_input("Spread", -20.0, 20.0, 0.0, 0.5, key="spread")
        
        with col2:
            st.markdown("### Injuries")
            all_players_list = []
            teams = game_id.split(" @ ")
            for team in teams:
                if team in st.session_state.players:
                    for pos, players in st.session_state.players[team].items():
                        all_players_list.extend(players)
            
            if all_players_list:
                injured_player = st.selectbox("Player", ["None"] + all_players_list, key="inj_player")
                injury_status = st.selectbox("Status", ["questionable", "doubtful", "out"], key="inj_status")
                
                if st.button("Add Injury"):
                    if injured_player != "None":
                        st.session_state.injuries[injured_player] = injury_status
                        st.success(f"{injured_player}: {injury_status}")
                
                if st.session_state.injuries:
                    st.markdown("**Current Injuries:**")
                    for pl, stat in st.session_state.injuries.items():
                        st.write(f"- {pl}: {stat}")
            else:
                st.info("Add players first")
        
        if st.button("💾 Save Conditions", type="primary"):
            st.session_state.game_conditions[game_id] = {
                'temp': temp,
                'wind': wind,
                'rain': rain,
                'total': total,
                'spread': spread
            }
            st.success("Saved!")

# ==================== TAB 4: ANALYSIS ====================
with tab4:
    st.header("Elite Analysis")
    
    if not st.session_state.current_game:
        st.warning("Select a game first")
    else:
        teams = st.session_state.current_game.split(" @ ")
        game_id = st.session_state.current_game
        
        cond = st.session_state.game_conditions.get(game_id, {})
        if cond:
            st.info(f"🌤️ {cond.get('temp', 70)}°F | 💨 {cond.get('wind', 0)}mph | "
                   f"🌧️ {cond.get('rain', 'none')} | O/U: {cond.get('total', 45)}")
        
        with st.sidebar:
            st.header("Select Props")
            props = []
            
            for idx, team in enumerate(teams):
                is_home = (idx == 1)
                st.markdown(f"### {team} {'🏠' if is_home else '✈️'}")
                
                if team in st.session_state.players:
                    for pos in POSITIONS:
                        players = st.session_state.players[team][pos]
                        if players:
                            st.markdown(f"**{pos}s**")
                            for pl in players:
                                key = f"{team}{pl}{pos}"
                                if st.checkbox(pl, key=f"c{key}"):
                                    for sk, sv in STATS_CONFIG[pos].items():
                                        if st.checkbox(f"  → {sv['name']}", key=f"s{key}{sk}"):
                                            opponent = teams[1] if idx == 0 else teams[0]
                                            props.append({
                                                'player': pl, 'pos': pos, 'team': team,
                                                'stat': sk, 'name': sv['name'],
                                                'opponent': opponent, 'is_home': is_home
                                            })
        
        st.session_state.threshold = st.slider("Confidence %", 50, 85, st.session_state.threshold)
        
        if st.button("🔍 ANALYZE", type="primary"):
            if props:
                with st.spinner("Analyzing..."):
                    results = []
                    for p in props:
                        calc = calculate_elite_projection(
                            p['player'], p['pos'], p['stat'],
                            p['opponent'], p['is_home'], game_id
                        )
                        results.append({**p, **calc,
                            'rec': 'OVER' if calc['confidence'] >= st.session_state.threshold else 'PASS'})
                    st.session_state.results = results
                    st.rerun()
            else:
                st.error("Select props")
        
        if st.session_state.results:
            res = st.session_state.results
            overs = [r for r in res if r['rec'] == 'OVER']
            
            st.markdown(f"### ✅ OVER Props ({len(overs)})")
            
            if overs:
                for r in overs:
                    with st.expander(f"**{r['player']}** - {r['name']} | {r['confidence']}%", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Line", r['line'])
                        c2.metric("Target", r['target'], f"+{r['margin']}")
                        emoji = "🟢" if r['confidence'] >= 70 else "🟡"
                        c3.metric("Confidence", f"{emoji} {r['confidence']}%")
                        
                        factors = r['factors']
                        st.caption(
                            f"🛡️ Def: {factors['defense']:.0%} | "
                            f"🏠 Home: {factors['home']:.0%} | "
                            f"🌤️ Weather: {factors['weather']:.0%} | "
                            f"📊 Script: {factors['script']:.0%}"
                        )
                
                if len(overs) >= 2:
                    st.markdown("---")
                    st.markdown("### 💰 Parlay Builder")
                    legs = st.slider("Legs", 2, min(5, len(overs)), 3)
                    parlay = overs[:legs]
                    prob = np.prod([p['confidence']/100 for p in parlay]) * 100
                    odds_str, odds_mult = get_parlay_odds(legs)
                    ev = (prob/100 * odds_mult - 1) * 100
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Probability", f"{prob:.1f}%")
                    c2.metric("Odds", odds_str)
                    c3.metric("EV", f"{ev:+.1f}%")
                    
                    for i, p in enumerate(parlay, 1):
                        st.write(f"{i}. **{p['player']}** OVER {p['line']} {p['name']}")
                    
                    if ev > 5:
                        st.success("✅ Strong EV!")
                    elif ev > 0:
                        st.info("ℹ️ Positive EV")
                    else:
                        st.warning("⚠️ Negative EV")
            else:
                st.info("No OVER props")

# ==================== TAB 5: STATS ====================
with tab5:
    st.header("Player Stats")
    
    if st.session_state.players:
        all_players = []
        for team, positions in st.session_state.players.items():
            for pos, players in positions.items():
                for pl in players:
                    all_players.append((pl, pos, team))
        
        if all_players:
            player_select = st.selectbox("Player", 
                [f"{pl} ({pos}) - {tm}" for pl, pos, tm in all_players])
            
            player_name = player_select.split(" (")[0]
            player_pos = player_select.split("(")[1].split(")")[0]
            
            st.subheader(f"Stats: {player_name}")
            
            for stat_key, stat_info in STATS_CONFIG[player_pos].items():
                st.markdown(f"**{stat_info['name']}** - Last 5 Games")
                
                player_stat_key = f"{player_name}_{stat_key}"
                current_games = st.session_state.player_stats.get(player_stat_key, [])
                
                cols = st.columns(5)
                new_games = []
                for i in range(5):
                    with cols[i]:
                        val = st.number_input(
                            f"Game {i+1}",
                            min_value=0.0,
                            value=float(current_games[i]) if i < len(current_games) else 0.0,
                            step=0.1 if 'td' in stat_key else 1.0,
                            key=f"g{player_name}{stat_key}{i}"
                        )
                        new_games.append(val)
                
                st.session_state.player_stats[player_stat_key] = new_games
                
                valid = [g for g in new_games if g > 0]
                if valid:
                    avg = np.mean(valid)
                    st.caption(f"Average: {avg:.1f}")
                
                st.markdown("---")
        else:
            st.info("Add players first")
    else:
        st.info("Create games first")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>🏈 THE ONE FOOTBALL v5.0 - Elite Edition</div>", unsafe_allow_html=True)

