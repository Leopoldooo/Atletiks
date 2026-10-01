from app.database import get_connection


def get_team_id(team_name):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM teams
            WHERE league_id = (
                SELECT id
                FROM leagues
                WHERE name = 'NBA'
            )
            AND LOWER(name) = LOWER(%s)
            LIMIT 1;
        """, (team_name,))

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def process_espn_game(response_data):
    events = response_data.get("events", [])

    if not events:
        return {
            "count": 0,
            "games": [],
            "error": "No events found in ESPN scoreboard response"
        }

    processed_games = []

    for event in events:
        event_id = event.get("id")

        competitions = event.get("competitions", [])

        if not competitions:
            continue

        competition = competitions[0]

        competitors = competition.get("competitors", [])

        home_team = None
        away_team = None

        for competitor in competitors:
            if competitor.get("homeAway") == "home":
                home_team = competitor

            elif competitor.get("homeAway") == "away":
                away_team = competitor

        if home_team is None or away_team is None:
            continue

        home_team_data = home_team.get("team", {})
        away_team_data = away_team.get("team", {})

        home_team_name = home_team_data.get("displayName")
        away_team_name = away_team_data.get("displayName")

        home_team_id = get_team_id(home_team_name)
        away_team_id = get_team_id(away_team_name)

        status_data = competition.get("status", {})
        status_type = status_data.get("type", {})

        state = status_type.get("state")

        current_period = status_data.get("period")
        game_clock = status_data.get("displayClock")

        # Only show period and clock while the game is live.
        if state != "in":
            current_period = None
            game_clock = None

        # Determine whether the game is in a quarter or overtime.
        if current_period is not None:
            if current_period <= 4:
                current_period_type = "Quarter"
            else:
                current_period_type = "Overtime"
        else:
            current_period_type = None

        processed_games.append({
            "external_id": event_id,
            "source_name": "espn",

            "scheduled_at": event.get("date"),

            "status": (
                status_type.get("description")
                or status_type.get("name")
                or "Scheduled"
            ),

            "current_period": current_period,
            "current_period_type": current_period_type,
            "game_clock": game_clock,

            "home_team_id": home_team_id,
            "away_team_id": away_team_id,

            "home_team_external_id": home_team_data.get("id"),
            "away_team_external_id": away_team_data.get("id"),

            "home_team_name": home_team_name,
            "away_team_name": away_team_name,

            "home_team_abbreviation": home_team_data.get(
                "abbreviation"
            ),
            "away_team_abbreviation": away_team_data.get(
                "abbreviation"
            ),

            "home_team_score": int(
                home_team.get("score", 0)
            ),

            "away_team_score": int(
                away_team.get("score", 0)
            ),

            "periods": process_periods(
                home_team,
                away_team
            )
        })

    return {
        "count": len(processed_games),
        "games": processed_games
    }


def process_periods(home_team, away_team):
    """
    Extract ESPN period scores.

    ESPN normally provides:
        period 1 = Q1
        period 2 = Q2
        period 3 = Q3
        period 4 = Q4

    Additional periods are treated as overtime.
    """

    home_linescores = home_team.get("linescores", [])
    away_linescores = away_team.get("linescores", [])

    periods = []

    number_of_periods = max(
        len(home_linescores),
        len(away_linescores)
    )

    for index in range(number_of_periods):

        period_number = index + 1

        home_period = (
            home_linescores[index]
            if index < len(home_linescores)
            else {}
        )

        away_period = (
            away_linescores[index]
            if index < len(away_linescores)
            else {}
        )

        if period_number <= 4:
            period_type = "Quarter"
        else:
            period_type = "Overtime"

        periods.append({
            "period_number": period_number,
            "period_type": period_type,

            "home_score": int(
                home_period.get("value", 0)
            ),

            "away_score": int(
                away_period.get("value", 0)
            )
        })

    return periods