from app.nba_processor import filter_nba_teams


sample_response = {
    "data": [
        {
            "id": 26,
            "conference": "West",
            "division": "Pacific",
            "city": "Sacramento",
            "name": "Kings",
            "full_name": "Sacramento Kings",
            "abbreviation": "SAC",
        },
        {
            "id": 37,
            "conference": "",
            "division": "",
            "city": "",
            "name": "Chicago Stags",
            "full_name": "Chicago Stags",
            "abbreviation": "CHS",
        },
        {
            "id": 2844,
            "conference": "",
            "division": "",
            "city": "Barcelona",
            "name": "Winterthur FC",
            "full_name": "Barcelona Winterthur FC",
            "abbreviation": "BAR",
        },
    ]
}


nba_teams = filter_nba_teams(sample_response)


print(f"NBA teams found: {len(nba_teams)}")

for team in nba_teams:
    print(
        team["short_name"],
        "-",
        team["name"]
    )