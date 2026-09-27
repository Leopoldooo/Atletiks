from app.database import get_connection


def get_or_create_player(player_data):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        external_id = player_data.get("external_id")
        source_name = player_data.get("source_name")

        cursor.execute("""
            SELECT id
            FROM players
            WHERE source_name = %s
              AND external_id = %s
            LIMIT 1;
        """, (
            source_name,
            str(external_id)
        ))

        result = cursor.fetchone()

        if result:
            player_id = result[0]

            cursor.execute("""
                UPDATE players
                SET
                    name = %s,
                    first_name = %s,
                    last_name = %s
                WHERE id = %s;
            """, (
                player_data.get("name"),
                player_data.get("first_name"),
                player_data.get("last_name"),
                player_id
            ))

            connection.commit()

            return player_id

        cursor.execute("""
            INSERT INTO players (
                sport_id,
                name,
                first_name,
                last_name,
                external_id,
                source_name
            )
            VALUES (
                (
                    SELECT id
                    FROM sports
                    WHERE name = 'Basketball'
                    LIMIT 1
                ),
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id;
        """, (
            player_data.get("name"),
            player_data.get("first_name"),
            player_data.get("last_name"),
            str(external_id),
            source_name
        ))

        player_id = cursor.fetchone()[0]

        connection.commit()

        return player_id

    finally:
        cursor.close()
        connection.close()


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
                LIMIT 1
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


def process_nba_players(processed_data):
    players = processed_data.get("players", [])

    processed_players = []

    for player in players:

        player_id = get_or_create_player(player)

        team_id = get_team_id(
            player.get("team_name")
        )

        processed_players.append({
            "player_id": player_id,

            "match_id": player.get("match_id"),

            "external_id": player.get("external_id"),
            "source_name": player.get("source_name"),

            "name": player.get("name"),

            "team_id": team_id,
            "team_external_id": player.get("team_external_id"),
            "team_name": player.get("team_name"),
            "team_abbreviation": player.get("team_abbreviation"),

            "jersey_number": player.get("jersey_number"),
            "position": player.get("position"),

            "is_starter": player.get("is_starter", False),

            "did_not_play": player.get(
                "did_not_play",
                False
            ),

            "did_not_play_reason": player.get(
                "did_not_play_reason"
            ),

            "minutes": player.get("minutes"),

            "points": player.get("points", 0),

            "field_goals_made": player.get(
                "field_goals_made",
                0
            ),

            "field_goals_attempted": player.get(
                "field_goals_attempted",
                0
            ),

            "three_pointers_made": player.get(
                "three_pointers_made",
                0
            ),

            "three_pointers_attempted": player.get(
                "three_pointers_attempted",
                0
            ),

            "free_throws_made": player.get(
                "free_throws_made",
                0
            ),

            "free_throws_attempted": player.get(
                "free_throws_attempted",
                0
            ),

            "rebounds": player.get("rebounds", 0),
            "assists": player.get("assists", 0),
            "turnovers": player.get("turnovers", 0),
            "steals": player.get("steals", 0),
            "blocks": player.get("blocks", 0),

            "offensive_rebounds": player.get(
                "offensive_rebounds",
                0
            ),

            "defensive_rebounds": player.get(
                "defensive_rebounds",
                0
            ),

            "personal_fouls": player.get(
                "personal_fouls",
                0
            ),

            "plus_minus": player.get(
                "plus_minus",
                0
            )
        })

    return {
        "match_id": processed_data.get("match_id"),
        "count": len(processed_players),
        "players": processed_players
    }