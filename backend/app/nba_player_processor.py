from datetime import timedelta

from app.database import get_connection


def get_or_create_player(player_data):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        external_id = player_data.get("external_id")
        source_name = player_data.get("source_name")

        if not external_id or not source_name:
            return None

        external_id = str(external_id)

        cursor.execute("""
            SELECT id
            FROM players
            WHERE source_name = %s
              AND external_id = %s
            LIMIT 1;
        """, (
            source_name,
            external_id
        ))

        result = cursor.fetchone()

        if result:
            player_id = result[0]

            new_name = player_data.get("name")

            cursor.execute("""
                UPDATE players
                SET
                    name = COALESCE(%s, name)
                WHERE id = %s;
            """, (
                new_name,
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
            external_id,
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

        if not team_name:
            return None

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


def get_match_date(match_id):
    if not match_id:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT scheduled_at::date
            FROM matches
            WHERE id = %s
            LIMIT 1;
        """, (match_id,))

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def update_player_team_history(
    player_id,
    team_id,
    match_date,
    jersey_number,
    position
):
    if not player_id or not team_id or not match_date:
        return

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Find the player's current active team relationship.
        cursor.execute("""
            SELECT
                id,
                team_id,
                start_date,
                end_date
            FROM player_teams
            WHERE player_id = %s
              AND end_date IS NULL
            ORDER BY start_date DESC, id DESC
            LIMIT 1;
        """, (player_id,))

        current_relationship = cursor.fetchone()

        # The player is already associated with this team.
        if current_relationship and current_relationship[1] == team_id:

            cursor.execute("""
                UPDATE player_teams
                SET
                    jersey_number = COALESCE(%s, jersey_number),
                    position = COALESCE(%s, position)
                WHERE id = %s;
            """, (
                jersey_number,
                position,
                current_relationship[0]
            ))

            connection.commit()

            return

        # The player has an active relationship with another team.
        #
        # Close the old relationship one day before the new team
        # relationship begins.
        if current_relationship:
            previous_team_end_date = match_date - timedelta(days=1)

            cursor.execute("""
                UPDATE player_teams
                SET
                    end_date = %s
                WHERE id = %s;
            """, (
                previous_team_end_date,
                current_relationship[0]
            ))

        # Check whether this exact player/team/start-date relationship
        # already exists.
        cursor.execute("""
            SELECT id
            FROM player_teams
            WHERE player_id = %s
              AND team_id = %s
              AND start_date = %s
            LIMIT 1;
        """, (
            player_id,
            team_id,
            match_date
        ))

        existing_relationship = cursor.fetchone()

        if existing_relationship:
            cursor.execute("""
                UPDATE player_teams
                SET
                    end_date = NULL,
                    jersey_number = COALESCE(%s, jersey_number),
                    position = COALESCE(%s, position)
                WHERE id = %s;
            """, (
                jersey_number,
                position,
                existing_relationship[0]
            ))

        else:
            cursor.execute("""
                INSERT INTO player_teams (
                    player_id,
                    team_id,
                    start_date,
                    end_date,
                    jersey_number,
                    position
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    NULL,
                    %s,
                    %s
                );
            """, (
                player_id,
                team_id,
                match_date,
                jersey_number,
                position
            ))

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def process_nba_players(processed_data):
    players = processed_data.get(
        "players",
        []
    )

    match_id = processed_data.get("match_id")
    match_date = get_match_date(match_id)

    processed_players = []

    for player in players:

        player_id = get_or_create_player(player)

        if player_id is None:
            continue

        team_id = get_team_id(
            player.get("team_name")
        )

        update_player_team_history(
            player_id=player_id,
            team_id=team_id,
            match_date=match_date,
            jersey_number=player.get("jersey_number"),
            position=player.get("position")
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
            "did_not_play": player.get("did_not_play", False),
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
            "rebounds": player.get(
                "rebounds",
                0
            ),
            "assists": player.get(
                "assists",
                0
            ),
            "turnovers": player.get(
                "turnovers",
                0
            ),
            "steals": player.get(
                "steals",
                0
            ),
            "blocks": player.get(
                "blocks",
                0
            ),
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