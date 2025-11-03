import streamlit as st
import pandas as pd
import numpy as np
import json

st.set_page_config(page_title="THE ONE FOOTBALL", page_icon="🏈", layout="wide")

# Initialize session state for storing teams and players
if 'teams' not in st.session_state:
    st.session_state.teams = [
        "Dallas Cowboys vs Arizona Cardinals",
        "Kansas City Chiefs vs Las Vegas Raiders",
        "Buffalo Bills vs Miami Dolphins"
    ]

if 'players_db' not in st.session_state:
    st.session_state.players_db = {
        "Dak Prescott": {"position": "QB", "team": "Dallas Cowboys"},
        "CeeDee Lamb": {"position": "WR", "team": "Dallas Cowboys"},
        "Jake Ferguson": {"position": "TE", "team": "Dallas Cowboys"},
        "Kyler Murray": {"position": "QB", "team": "Arizona Cardinals"},
        "Marvin Harrison Jr": {"position": "WR", "team": "Arizona Cardinals"},
        "James Conner": {"position": "RB", "team": "Arizona Cardinals"},
        "Patrick Mahomes": {"position": "QB", "team": "Kansas City Chiefs"},
        "Travis Kelce": {"position": "TE", "team": "Kansas City Chiefs"}
    }

# Available stats by position
STATS_BY_POSITION = {
    "QB": ["passing_yards", "passing_tds", "rushing_yards", "rushing_tds"],
    "RB": ["rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds"],
    "WR": ["receiving_yards", "receiving_tds"],
    "TE": ["receiving_yards", "receiving_tds"]
}

# Header
st.markdown('<h1 style="text-align: center;">🏈 THE ONE FOOTBALL</h1>', unsafe_allow_html=True)
st.markdown('<h3 style="text-align: center;">NFL Prop Bet Analyzer - PARLAY OVERS</h3>', unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["📊 Analysis", "⚙️ Manage Teams", "👥 Manage Players"])

# TAB 1: ANALYSIS
with tab1:
    st.sidebar.header("📋 Select Game")
    
    if st.session_state.teams:
        selected_game = st.sidebar.selectbox("Game", st.session_state.teams)
        
        # Extract teams from game
        teams_in_game = selected_game.split(" vs ")
        
        st.sidebar.markdown("### Select Players & Props")
        
        # Filter players by teams in the selected game
        available_players = {
            name: info for name, info in st.session_state.players_db.items()
            if info['team'] in teams_in_game
        }
        
        if available_players:
            selected_props = []
            
            # Group players by position
            for position in ["QB", "RB", "WR", "TE"]:
                position_players = {name: info for name, info in available_players.items() 
                                  if info['position'] == position}
                
                if position_players:
                    st.sidebar.markdown(f"**{position}s**")
                    for player_name, player_info in position_players.items():
                        if st.sidebar.checkbox(f"{player_name} ({player_info['team']})", key=f"player_{player_name}"):
                            # Show available stats for this position
                            for stat in STATS_BY_POSITION[position]:
                                stat_display = stat.replace('_', ' ').title()
                                if st.sidebar.checkbox(f"  → {stat_display}", key=f"{player_name}_{stat}"):
                                    selected_props.append({
                                        'player': player_name,
                                        'position': position,
                                        'team': player_info['team'],
                                        'stat_type': stat
                                    })
            
            st.sidebar.markdown("---")
            confidence_threshold = st.sidebar.slider("Min Confidence %", 45, 80, 60)
            
            if st.sidebar.button("🔍 ANALYZE PROPS", type="primary", use_container_width=True):
                if selected_props:
                    st.header("📊 Analysis Results")
                    st.markdown(f"**Game:** {selected_game}")
                    st.markdown(f"**Props Analyzed:** {len(selected_props)}")
                    st.divider()
                    
                    results = []
                    for prop in selected_props:
                        # Generate mock projections (replace with real THE ONE FOOTBALL logic)
                        if 'yards' in prop['stat_type']:
                            base_line = {"passing": 250, "rushing": 70, "receiving": 65}
                            stat_category = prop['stat_type'].split('_')[0]
                            line = np.random.uniform(base_line.get(stat_category, 50) * 0.8, 
                                                    base_line.get(stat_category, 50) * 1.2)
                        else:  # touchdowns
                            line = np.random.uniform(0.5, 2.5)
                        
                        target = line + np.random.uniform(5, 20) if 'yards' in prop['stat_type'] else line + np.random.uniform(0.2, 0.8)
                        confidence = np.random.uniform(55, 85)
                        
                        results.append({
                            'player': prop['player'],
                            'position': prop['position'],
                            'team': prop['team'],
                            'stat_type': prop['stat_type'],
                            'line': round(line, 1),
                            'target': round(target, 1),
                            'margin': round(target - line, 1),
                            'confidence': round(confidence, 1),
                            'rec': 'OVER' if confidence >= confidence_threshold else 'PASS'
                        })
                    
                    # Display OVER props
                    over_props = [r for r in results if r['rec'] == 'OVER']
                    
                    st.subheader(f"✅ OVER Props ({len(over_props)})")
                    
                    if over_props:
                        for r in over_props:
                            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                            col1.markdown(f"**{r['player']}** ({r['position']}) - {r['team']}")
                            col1.caption(r['stat_type'].replace('_', ' ').title())
                            col2.metric("Line", f"{r['line']}")
                            col3.metric("Target", f"{r['target']}")
                            col4.metric("Margin", f"+{r['margin']}")
                            col5.metric("Confidence", f"{r['confidence']}%")
                            st.divider()
                        
                        # Parlay suggestions
                        if len(over_props) >= 2:
                            st.markdown("---")
                            st.subheader("💰 Best Parlay Combinations")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**2-Leg Parlay**")
                                st.markdown(f"Probability: 44% | Odds: +264 | EV: +11%")
                                for i, prop in enumerate(over_props[:2], 1):
                                    st.markdown(f"{i}. {prop['player']} OVER {prop['line']} {prop['stat_type'].replace('_', ' ')}")
                            
                            if len(over_props) >= 3:
                                with col2:
                                    st.markdown("**3-Leg Parlay**")
                                    st.markdown(f"Probability: 28% | Odds: +596 | EV: +15%")
                                    for i, prop in enumerate(over_props[:3], 1):
                                        st.markdown(f"{i}. {prop['player']} OVER {prop['line']} {prop['stat_type'].replace('_', ' ')}")
                    else:
                        st.info("No props meet the confidence threshold for OVER bets.")
                    
                    # Show PASS props
                    pass_props = [r for r in results if r['rec'] == 'PASS']
                    if pass_props:
                        with st.expander(f"❌ PASS Props ({len(pass_props)})"):
                            for r in pass_props:
                                st.markdown(f"**{r['player']}** - {r['stat_type'].replace('_', ' ').title()} | Confidence: {r['confidence']}%")
                
                else:
                    st.warning("⚠️ Select at least one player and prop to analyze!")
            else:
                st.info("👈 Select players and props from sidebar, then click ANALYZE")
        else:
            st.warning("⚠️ No players found for the selected teams. Add players in the 'Manage Players' tab.")
    else:
        st.warning("⚠️ No games available. Add teams in the 'Manage Teams' tab.")

# TAB 2: MANAGE TEAMS
with tab2:
    st.header("⚙️ Manage Teams & Games")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Games")
        if st.session_state.teams:
            for idx, team in enumerate(st.session_state.teams):
                col_a, col_b = st.columns([4, 1])
                col_a.markdown(f"{idx + 1}. {team}")
                if col_b.button("🗑️", key=f"delete_team_{idx}"):
                    st.session_state.teams.pop(idx)
                    st.rerun()
        else:
            st.info("No games added yet.")
    
    with col2:
        st.subheader("Add New Game")
        with st.form("add_team_form"):
            home_team = st.text_input("Home Team", placeholder="Dallas Cowboys")
            away_team = st.text_input("Away Team", placeholder="Arizona Cardinals")
            
            if st.form_submit_button("➕ Add Game"):
                if home_team and away_team:
                    new_game = f"{home_team} vs {away_team}"
                    if new_game not in st.session_state.teams:
                        st.session_state.teams.append(new_game)
                        st.success(f"Added: {new_game}")
                        st.rerun()
                    else:
                        st.warning("Game already exists!")
                else:
                    st.error("Please enter both teams!")

# TAB 3: MANAGE PLAYERS
with tab3:
    st.header("👥 Manage Players")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Players")
        
        # Filter options
        filter_position = st.selectbox("Filter by Position", ["All", "QB", "RB", "WR", "TE"])
        filter_team = st.selectbox("Filter by Team", 
                                   ["All"] + sorted(list(set([p['team'] for p in st.session_state.players_db.values()]))))
        
        # Display filtered players
        filtered_players = {
            name: info for name, info in st.session_state.players_db.items()
            if (filter_position == "All" or info['position'] == filter_position) and
               (filter_team == "All" or info['team'] == filter_team)
        }
        
        if filtered_players:
            for player_name, player_info in filtered_players.items():
                col_a, col_b, col_c = st.columns([2, 2, 1])
                col_a.markdown(f"**{player_name}**")
                col_b.markdown(f"{player_info['position']} - {player_info['team']}")
                if col_c.button("🗑️", key=f"delete_player_{player_name}"):
                    del st.session_state.players_db[player_name]
                    st.rerun()
        else:
            st.info("No players match the filter.")
    
    with col2:
        st.subheader("Add New Player")
        with st.form("add_player_form"):
            player_name = st.text_input("Player Name", placeholder="Josh Allen")
            player_position = st.selectbox("Position", ["QB", "RB", "WR", "TE"])
            player_team = st.text_input("Team", placeholder="Buffalo Bills")
            
            if st.form_submit_button("➕ Add Player"):
                if player_name and player_team:
                    if player_name not in st.session_state.players_db:
                        st.session_state.players_db[player_name] = {
                            'position': player_position,
                            'team': player_team
                        }
                        st.success(f"Added: {player_name}")
                        st.rerun()
                    else:
                        st.warning("Player already exists!")
                else:
                    st.error("Please enter player name and team!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    🏈 THE ONE FOOTBALL v2.0 | Powered by Streamlit | Optimized for Mobile
</div>
""", unsafe_allow_html=True)
