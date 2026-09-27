NBA_ABBREVIATIONS = {
    "ATL",
    "BOS",
    "BKN",
    "CHA",
    "CHI",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GSW",
    "HOU",
    "IND",
    "LAC",
    "LAL",
    "MEM",
    "MIA",
    "MIL",
    "MIN",
    "NOP",
    "NYK",
    "OKC",
    "ORL",
    "PHI",
    "PHX",
    "POR",
    "SAC",
    "SAS",
    "TOR",
    "UTA",
    "WAS",
}


def filter_nba_teams(response_data):
    teams = response_data.get("data", [])

    nba_teams = []

    for team in teams:
        abbreviation = team.get("abbreviation")
        conference = team.get("conference")
        division = team.get("division")

        if abbreviation not in NBA_ABBREVIATIONS:
            continue

        if not conference or not division:
            continue

        nba_teams.append({
            "external_id": team.get("id"),
            "name": team.get("full_name"),
            "short_name": abbreviation,
            "country": "United States",
            "conference": conference,
            "division": division,
        })

    return nba_teams