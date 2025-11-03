import streamlit as st
import numpy as np

st.set_page_config(page_title="THE ONE FOOTBALL", page_icon="🏈", layout="wide")

NFL_TEAMS = ["Arizona Cardinals", "Dallas Cowboys", "Baltimore Ravens", "Buffalo Bills",
    "Kansas City Chiefs", "Philadelphia Eagles", "San Francisco 49ers", "Miami Dolphins",
    "New York Giants", "New York Jets", "Los Angeles Rams", "Green Bay Packers"]

POSITIONS = ["QB", "RB", "WR", "TE"]

POSITION_STATS = {
    "QB": ["passing_yards", "passing_tds", "rushing_yards"],
    "RB": ["rushing_yards", "rushing_tds", "receiving_yards"],
    "WR": ["receiving_yards", "receiving_tds", "receptions"],
    "TE": ["receiving_yards", "receiving_tds", "receptions"]
}

STATS = {
    "passing_yards": {"name": "Passing Yards", "base": 250},
    "passing_tds": {"name": "Passing TDs", "base": 1.5},
    "rushing_yards": {"name": "Rushing Yards", "base": 65},
    "rushing_tds": {"name": "Rushing TDs", "base": 0.5},
    "receiving_yards": {"name": "Receiving Yards", "base": 55},
    "receiving_tds": {"name": "Receiving TDs", "base": 0.4},
    "receptions": {"name": "Receptions", "base": 5.5}
}

QUICK_PLAYERS = {
    "QB": ["Dak Prescott", "Kyler Murray", "Patrick Mahomes"],
    "RB": ["Javonte Williams", "Bam Knight", "Saquon Barkley"],
    "WR": ["CeeDee Lamb", "Marvin Harrison Jr.", "George Pickens"],
    "TE": ["Jake Ferguson", "Trey McBride", "Travis Kelce"]
}

if 'games' not in st.session_state:
    st.session_state.games = []
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'conditions' not in st.session_state:
    st.session_state.conditions = {}
if 'current' not in st.session_state:
    st.session_state.current = None
if 'results' not in st.session_state:
    st.session_state.results = []

def calculate_projection(player, position, stat, opponent, is_home, game_id):
    base = STATS[stat]['base']
    
    if position == "QB" and stat == "rushing_yards":
        base = 25
    elif position == "RB" and stat == "rushing_yards":
        base = 75
    elif position == "RB" and stat == "receiving_yards":
        base = 30
    elif position == "WR" and stat == "receiving_yards":
        base = 65
    elif position == "WR" and stat == "receptions":
        base = 6.0
    elif position == "TE" and stat == "receiving_yards":
        base = 45
    elif position == "TE" and stat == "receptions":
        base = 5.0
    
    home_mult = 1.07 if is_home else 1.0
    
    conditions = st.session_state.conditions.get(game_id, {})
    total = conditions.get('total', 45)
    
    if total >= 50:
        script_mult = 1.12
    elif total >= 47:
        script_mult = 1.08
    else:
        script_mult = 1.0
    
    projection = base * home_mult * script_mult
    line = max(0, np.random.normal(projection, 5))
    target = line * 1.10
    
    confidence = 65
    if is_home:
        confidence += 3
    if script_mult > 1.08:
        confidence += 5
    confidence = np.clip(confidence + np.random.uniform(-3, 3), 55, 85)
    
    return {
        'player': player,
        'position': position,
        'stat': STATS[stat]['name'],
        'line': round(line, 1),
        'target': round(target, 1),
        'margin': round(target - line, 1),
        'confidence': round(confidence, 1),
        'opponent': opponent,
        'is_home': is_home
    }

def get_parlay_odds(num_legs):
    odds_table = {
        2: ("+264", 2.64),
        3: ("+596", 5.96),
        4: ("+1228", 11.28),
        5: ("+2435", 23.35),
        6: ("+4700", 47.0),
        8: ("+9500", 95.0),
        10: ("+25000", 250.0),
        12: ("+40000", 400.0)
    }
    return odds_table.get(num_legs, ("+40000", 400.0))

st.title("🏈 THE ONE FOOTBALL")
st.caption("Built to Win 💰")

col1, col2, col3 = st.columns(3)
col1.metric("Games", len(st.session_state.games))
col2.metric("Props Analyzed", len(st.session_state.results))
col3.metric("Version", "FINAL")

tab1, tab2, tab3 = st.tabs(["Setup", "Players", "Results"])

with tab1:
    st.header("Game Setup")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Create Game")
        away_team = st.selectbox("Away Team", ["Select..."] + NFL_TEAMS, key="away_team")
        home_team = st.selectbox("Home Team", ["Select..."] + NFL_TEAMS, key="home_team")
        
        if st.button("Create Game", type="primary"):
            if away_team != "Select..." and home_team != "Select..." and away_team != home_team:
                game_name = f"{away_team} @ {home_team}"
                if game_name not in st.session_state.games:
                    st.session_state.games.append(game_name)
                    st.session_state.players[game_name] = []
                    st.success(f"Created: {game_name}")
                    st.rerun()
            else:
                st.error("Select two different teams")
    
    with col_right:
        st.subheader("Set Conditions")
        if st.session_state.games:
            selected_game = st.selectbox("Select Game", st.session_state.games)
            over_under = st.number_input("Over/Under Total", 30.0, 65.0, 48.5, 0.5)
            
            if st.button("Activate Game", type="primary"):
                st.session_state.conditions[selected_game] = {'total': over_under}
                st.session_state.current = selected_game
                st.success(f"Activated: {selected_game}")
                st.rerun()
        else:
            st.info("Create a game first")
    
    if st.session_state.current:
        st.success(f"**Active Game:** {st.session_state.current}")

with tab2:
    st.header("Add Players")
    
    if not st.session_state.current:
        st.warning("Please set up and activate a game first")
    else:
        teams = st.session_state.current.split(" @ ")
        
        col_add, col_list = st.columns([1, 1])
        
        with col_add:
            st.subheader("Add New Player")
            player_team = st.selectbox("Team", teams)
            add_method = st.radio("Method", ["Quick Select", "Manual Entry"], horizontal=True)
            
            if add_method == "Quick Select":
                player_pos = st.selectbox("Position", POSITIONS, key="quick_pos")
                player_name = st.selectbox("Player", QUICK_PLAYERS[player_pos], key="quick_name")
            else:
                player_pos = st.selectbox("Position", POSITIONS, key="manual_pos")
                player_name = st.text_input("Player Name", key="manual_name")
            
            if st.button("ADD & ANALYZE", type="primary"):
                if player_name and player_name != "Select...":
                    if st.session_state.current not in st.session_state.players:
                        st.session_state.players[st.session_state.current] = []
                    
                    existing_names = [p['name'] for p in st.session_state.players[st.session_state.current]]
                    
                    if player_name not in existing_names:
                        st.session_state.players[st.session_state.current].append({
                            'name': player_name,
                            'position': player_pos,
                            'team': player_team
                        })
                        
                        is_home_team = (player_team == teams[1])
                        opponent_team = teams[1] if player_team == teams[0] else teams[0]
                        
                        for stat_key in POSITION_STATS[player_pos]:
                            result = calculate_projection(
                                player_name, 
                                player_pos, 
                                stat_key, 
                                opponent_team, 
                                is_home_team, 
                                st.session_state.current
                            )
                            st.session_state.results.append(result)
                        
                        st.success(f"Added and analyzed: {player_name}")
                        st.rerun()
                    else:
                        st.error(f"{player_name} already added")
                else:
                    st.error("Enter a player name")
        
        with col_list:
            st.subheader("Current Players")
            if st.session_state.current in st.session_state.players:
                player_list = st.session_state.players[st.session_state.current]
                if player_list:
                    for idx, player_info in enumerate(player_list):
                        col_name, col_del = st.columns([4, 1])
                        col_name.write(f"{player_info['name']} ({player_info['position']})")
                        if col_del.button("Delete", key=f"delete_{idx}"):
                            removed_name = player_list[idx]['name']
                            player_list.pop(idx)
                            st.session_state.results = [
                                r for r in st.session_state.results 
                                if r['player'] != removed_name
                            ]
                            st.rerun()
                else:
                    st.info("No players added yet")

with tab3:
    st.header("Analysis Results")
    
    if not st.session_state.results:
        st.info("Add players to see analysis results")
    else:
        confidence_threshold = st.slider("Minimum Confidence %", 50, 85, 60, 5)
        filtered_results = [r for r in st.session_state.results if r['confidence'] >= confidence_threshold]
        
        st.markdown(f"### {len(filtered_results)} Props Above {confidence_threshold}% Confidence")
        
        if filtered_results:
            for result in filtered_results:
                emoji = "🟢" if result['confidence'] >= 70 else "🟡"
                expander_title = f"{emoji} {result['player']} - {result['stat']} | {result['confidence']}%"
                
                with st.expander(expander_title):
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric("Line", result['line'])
                    metric_col2.metric("Target", result['target'])
                    metric_col3.metric("Confidence", f"{result['confidence']}%")
            
            if len(filtered_results) >= 2:
                st.markdown("---")
                st.markdown("## Parlay Builder")
                
                num_legs = st.slider("Number of Legs", 2, min(12, len(filtered_results)), 6)
                parlay_props = filtered_results[:num_legs]
                
                confidences = [p['confidence'] / 100 for p in parlay_props]
                probability = np.prod(confidences) * 100
                
                odds_string, multiplier = get_parlay_odds(num_legs)
                
                expected_value = (probability / 100 * multiplier - 1) * 100
                
                metric_a, metric_b, metric_c = st.columns(3)
                metric_a.metric("Hit Probability", f"{probability:.2f}%")
                metric_b.metric("Payout Odds", odds_string)
                metric_c.metric("Expected Value", f"{expected_value:+.0f}%")
                
                st.markdown("### Your Parlay Legs:")
                for leg_num, prop in enumerate(parlay_props, 1):
                    st.write(f"{leg_num}. {prop['player']} OVER {prop['line']} {prop['stat']}")
                
                bet_amount = st.number_input("Bet Amount ($)", 10, 1000, 100, 10)
                potential_win = bet_amount * multiplier
                st.success(f"**Potential Win: ${potential_win:,.0f}**")
                
                st.markdown("### Copy to Sportsbook:")
                text_output = ""
                for leg_num, prop in enumerate(parlay_props, 1):
                    line_text = f"{leg_num}. {prop['player']} OVER {prop['line']} {prop['stat']}
"
                    text_output = text_output + line_text
                st.code(text_output)
        else:
            st.warning(f"No props meet the {confidence_threshold}% confidence threshold")

st.markdown("---")
st.caption("🏈 THE ONE FOOTBALL - Final Version") 