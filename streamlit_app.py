import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="THE ONE FOOTBALL", page_icon="🏈", layout="wide")

st.markdown('<h1 style="text-align: center;">🏈 THE ONE FOOTBALL</h1>', unsafe_allow_html=True)
st.markdown('<h3 style="text-align: center;">NFL Prop Bet Analyzer</h3>', unsafe_allow_html=True)

st.sidebar.header("📋 Select Game")
games = ["Dallas Cowboys vs Arizona Cardinals", "Kansas City Chiefs vs Las Vegas Raiders"]
game = st.sidebar.selectbox("Game", games)

st.sidebar.header("Select Players")
players = {
    "Dak Prescott": ["passing_yards", "passing_tds"],
    "CeeDee Lamb": ["receiving_yards"],
    "Kyler Murray": ["passing_yards"]
}

selected = []
for player, props in players.items():
    if st.sidebar.checkbox(player):
        for prop in props:
            if st.sidebar.checkbox(f"  {prop.replace('_', ' ').title()}", key=f"{player}_{prop}"):
                selected.append({'player': player, 'prop': prop})

if st.sidebar.button("🔍 ANALYZE", type="primary"):
    if selected:
        st.header("📊 Results")
        for item in selected:
            line = round(np.random.uniform(50, 300), 1)
            target = round(line + np.random.uniform(5, 20), 1)
            conf = round(np.random.uniform(55, 85), 1)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Player", item['player'])
            col2.metric("Line", line)
            col3.metric("Target", target, f"+{target-line:.1f}")
            col4.metric("Confidence", f"{conf}%")
            st.divider()
    else:
        st.warning("Select players first!")
else:
    st.info("👈 Select game and players, then click ANALYZE")
