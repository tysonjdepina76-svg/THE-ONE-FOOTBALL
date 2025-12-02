import streamlit as st
import pandas as pd
from main import project_game

st.set_page_config(page_title="THE ONE FOOTBALL – NFL Prop Analyzer", layout="wide")

st.title("THE ONE FOOTBALL – NFL Prop Analyzer")
st.write("Run the NFL FINAL TEMPLATE with matchup, DVOA, injuries, and game-flow adjustments.")

st.sidebar.header("Game Selection")
home_team = st.sidebar.text_input("Home Team", value="Lions")
away_team = st.sidebar.text_input("Away Team", value="Cowboys")
game_id = st.sidebar.text_input("Game ID", value="2025-12-04-DAL@DET")

if st.sidebar.button("Run Projections"):
    with st.spinner("Running projections..."):
        try:
            projections = project_game(game_id, home_team, away_team)

            rows = []
            for player, proj in projections.items():
                row = {"Player": player}
                row.update(proj)
                rows.append(row)
            df = pd.DataFrame(rows)

            front_cols = [c for c in [
                "Player", "team", "position", "passing_yards", "passing_tds",
                "rushing_yards", "receiving_yards", "total_yards",
                "receptions", "hit_prob"
            ] if c in df.columns]
            other_cols = [c for c in df.columns if c not in front_cols]
            df = df[front_cols + other_cols]

            st.subheader(f"Projections – {home_team} vs {away_team}")
            st.dataframe(df, use_container_width=True)

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Projections as CSV",
                data=csv_data,
                file_name=f"{home_team}_vs_{away_team}_projections.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error while running projections: {e}")
else:
    st.info("Enter teams and game ID on the left, then click 'Run Projections'.")