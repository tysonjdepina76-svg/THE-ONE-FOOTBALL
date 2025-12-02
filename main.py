from data_ingestion import (
    fetch_player_baselines,
    fetch_dvoa_stats,
    fetch_injury_report,
    fetch_game_script,
    fetch_game_matchup_advanced,
    fetch_efficiency_metrics,
)
from projection_adjustments import adjust_projections


def project_game(game_id, home_team, away_team):
    base_projs = fetch_player_baselines(game_id)

    dvoa_home = fetch_dvoa_stats(home_team)
    dvoa_away = fetch_dvoa_stats(away_team)

    matchup_stats = fetch_game_matchup_advanced(home_team, away_team)
    injuries_home = fetch_injury_report(home_team)
    injuries_away = fetch_injury_report(away_team)
    game_script = fetch_game_script(game_id)
    efficiency_home = fetch_efficiency_metrics(home_team)
    efficiency_away = fetch_efficiency_metrics(away_team)

    offense_stats_home = {"team": home_team, **dvoa_home}
    offense_stats_away = {"team": away_team, **dvoa_away}
    defense_stats_home = {
        "team": home_team,
        "pressure_rate": matchup_stats["pressure_rate_home_def"],
        "defense_dvoa": dvoa_home["defense_dvoa"],
    }
    defense_stats_away = {
        "team": away_team,
        "pressure_rate": matchup_stats["pressure_rate_away_def"],
        "defense_dvoa": dvoa_away["defense_dvoa"],
    }
    coverage_scheme_home = {"type": matchup_stats["coverage_type_home_def"]}
    coverage_scheme_away = {"type": matchup_stats["coverage_type_away_def"]}

    base_proj_home = {p: v for p, v in base_projs.items() if v["team"] == home_team}
    base_proj_away = {p: v for p, v in base_projs.items() if v["team"] == away_team}

    adjusted_home = adjust_projections(
        base_proj_home,
        defense_stats_away,
        offense_stats_home,
        injuries_home,
        game_script,
        coverage_scheme_away,
        efficiency_away,
    )
    adjusted_away = adjust_projections(
        base_proj_away,
        defense_stats_home,
        offense_stats_away,
        injuries_away,
        game_script,
        coverage_scheme_home,
        efficiency_home,
    )

    combined = {**adjusted_home, **adjusted_away}
    return combined


if __name__ == "__main__":
    import json
    print(json.dumps(project_game("2025-12-04-DAL@DET", "Lions", "Cowboys"), indent=2))