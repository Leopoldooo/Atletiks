from app.database import get_connection


def get_match_id(external_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM matches
            WHERE source_name = 'espn'
              AND external_id = %s
            LIMIT 1;
        """, (str(external_id),))

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def parse_made_attempted(value):
    """
    Converts ESPN stat values such as:
        "7-17" -> (7, 17)
        "2-6"  -> (2, 6)

    Returns (0, 0) if the value is missing or invalid.
    """

    if value is None:
        return 0, 0

    value = str(value)

    if "-" not in value:
        return 0, 0

    try:
        made, attempted = value.split("-", 1)

        return int(made), int(attempted)

    except (ValueError, TypeError):
        return 0, 0


def process_nba_player_stats(response_data):
    boxscore = response_data.get("boxscore", {})
    players = boxscore.get("players", [])

    # ESPN event/game ID
    game_external_id = response_data.get("header", {}).get("id")

    # Find the corresponding Atletiks match
    match_id = get_match_id(game_external_id)

    processed_players = []

    for team_data in players:
        team = team_data.get("team", {})

        team_external_id = team.get("id")
        team_name = team.get("displayName")
        team_abbreviation = team.get("abbreviation")

        statistics_groups = team_data.get("statistics", [])

        for statistics_group in statistics_groups:
            keys = statistics_group.get("keys", [])
            athletes = statistics_group.get("athletes", [])

            for athlete_data in athletes:
                athlete = athlete_data.get("athlete", {})
                stats = athlete_data.get("stats", [])

                stat_map = {}

                for index, key in enumerate(keys):
                    if index < len(stats):
                        stat_map[key] = stats[index]

                # Parse FG, 3PT, and FT values
                # Example: "7-17" becomes made=7, attempted=17
                field_goals_made, field_goals_attempted = (
                    parse_made_attempted(
                        stat_map.get(
                            "fieldGoalsMade-fieldGoalsAttempted"
                        )
                    )
                )

                three_pointers_made, three_pointers_attempted = (
                    parse_made_attempted(
                        stat_map.get(
                            "threePointFieldGoalsMade-threePointFieldGoalsAttempted"
                        )
                    )
                )

                free_throws_made, free_throws_attempted = (
                    parse_made_attempted(
                        stat_map.get(
                            "freeThrowsMade-freeThrowsAttempted"
                        )
                    )
                )

                processed_players.append({
                    "match_id": match_id,

                    "external_id": athlete.get("id"),
                    "source_name": "espn",

                    "name": athlete.get("displayName"),

                    "team_external_id": team_external_id,
                    "team_name": team_name,
                    "team_abbreviation": team_abbreviation,

                    "jersey_number": athlete.get("jersey"),

                    "position": (
                        athlete.get("position", {}).get("displayName")
                        if athlete.get("position")
                        else None
                    ),

                    "is_starter": athlete_data.get("starter", False),

                    "did_not_play": athlete_data.get(
                        "didNotPlay",
                        False
                    ),

                    "did_not_play_reason": athlete_data.get(
                        "reason"
                    ),

                    "minutes": stat_map.get("minutes"),

                    "points": stat_map.get("points", 0),

                    "field_goals_made": field_goals_made,
                    "field_goals_attempted": field_goals_attempted,

                    "three_pointers_made": three_pointers_made,
                    "three_pointers_attempted": three_pointers_attempted,

                    "free_throws_made": free_throws_made,
                    "free_throws_attempted": free_throws_attempted,

                    "rebounds": stat_map.get("rebounds", 0),
                    "assists": stat_map.get("assists", 0),
                    "turnovers": stat_map.get("turnovers", 0),
                    "steals": stat_map.get("steals", 0),
                    "blocks": stat_map.get("blocks", 0),

                    "offensive_rebounds": stat_map.get(
                        "offensiveRebounds",
                        0
                    ),

                    "defensive_rebounds": stat_map.get(
                        "defensiveRebounds",
                        0
                    ),

                    "personal_fouls": stat_map.get(
                        "fouls",
                        0
                    ),

                    "plus_minus": stat_map.get(
                        "plusMinus",
                        0
                    )
                })

    return {
        "match_external_id": game_external_id,
        "match_id": match_id,
        "count": len(processed_players),
        "players": processed_players
    }