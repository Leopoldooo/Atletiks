from app.database import get_connection


def get_nba_team_id(external_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM teams
            WHERE source_name = 'balldontlie'
              AND external_id = %s
              AND league_id = (
                  SELECT id
                  FROM leagues
                  WHERE name = 'NBA'
              )
            LIMIT 1;
        """, (str(external_id),))

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def process_nba_games(response_data):
    games = response_data.get("data", [])

    processed_games = []

    for game in games:
        home_team = game.get("home_team") or {}
        visitor_team = game.get("visitor_team") or {}

        home_external_id = home_team.get("id")
        away_external_id = visitor_team.get("id")

        home_team_id = get_nba_team_id(home_external_id)
        away_team_id = get_nba_team_id(away_external_id)

        periods = []

        for period_number in range(1, 5):
            periods.append({
                "period_number": period_number,
                "period_type": "Quarter",
                "home_score": game.get(f"home_q{period_number}"),
                "away_score": game.get(f"visitor_q{period_number}")
            })

        for overtime_number in range(1, 4):
            home_score = game.get(f"home_ot{overtime_number}")
            away_score = game.get(f"visitor_ot{overtime_number}")

            if home_score is not None or away_score is not None:
                periods.append({
                    "period_number": overtime_number,
                    "period_type": "Overtime",
                    "home_score": home_score,
                    "away_score": away_score
                })

        processed_games.append({
            "external_id": game.get("id"),
            "source_name": "balldontlie",

            "scheduled_at": game.get("datetime") or game.get("date"),
            "status": game.get("status"),
            "period": game.get("period"),
            "time": game.get("time"),
            "postseason": game.get("postseason", False),

            "home_team_external_id": home_external_id,
            "home_team_id": home_team_id,
            "home_team_name": home_team.get("full_name"),
            "home_team_abbreviation": home_team.get("abbreviation"),

            "away_team_external_id": away_external_id,
            "away_team_id": away_team_id,
            "away_team_name": visitor_team.get("full_name"),
            "away_team_abbreviation": visitor_team.get("abbreviation"),

            "home_team_score": game.get("home_team_score", 0),
            "away_team_score": game.get("visitor_team_score", 0),

            "periods": periods
        })

    return processed_games