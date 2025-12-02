import requests
from config_api_keys import (
    SPORTSDATAIO_API_KEY,
    DVOA_API_KEY,
    INJURY_API_KEY,
    ADVANCED_METRICS_API_KEY,
)


def fetch_player_baselines(game_id: str):
    url = f"https://api.sportsdata.io/v3/nfl/projections/json/PlayerGameProjectionStatsByWeek/{game_id}"
    headers = {"Ocp-Apim-Subscription-Key": SPORTSDATAIO_API_KEY}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    players = {}
    for row in data:
        name = row.get("Name")
        if not name:
            continue
        team = row.get("Team")
        pos = row.get("Position")

        players[name] = {
            "team": team,
            "position": pos,
            "passing_yards": row.get("PassingYards", 0.0),
            "passing_tds": row.get("PassingTouchdowns", 0.0),
            "rushing_yards": row.get("RushingYards", 0.0),
            "receiving_yards": row.get("ReceivingYards", 0.0),
            "receptions": row.get("Receptions", 0.0),
            "hit_prob": 0.6,
        }
    return players


def fetch_dvoa_stats(team: str):
    url = f"https://api.dvoadata.com/team/{team}"
    headers = {"Authorization": f"Bearer {DVOA_API_KEY}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    return {
        "offense_dvoa": data.get("offense_dvoa", 0.0),
        "defense_dvoa": data.get("defense_dvoa", 0.0),
    }


def fetch_injury_report(team: str):
    url = f"https://api.sportsdata.io/v3/nfl/injuries/json/InjuriesByTeam/{team}"
    headers = {"Ocp-Apim-Subscription-Key": INJURY_API_KEY or SPORTSDATAIO_API_KEY}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    injuries = {"OLINE": "healthy"}
    for row in data:
        pos = row.get("Position", "")
        status = row.get("InjuryStatus", "")
        if pos in ["C", "G", "T", "OL"]:
            if status in ["Questionable", "Doubtful", "Out"]:
                injuries["OLINE"] = "injured"
    return injuries


def fetch_game_script