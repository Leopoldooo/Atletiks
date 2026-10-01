from app.database import get_connection


def get_participant_result(match_status, winner):
    """
    Determine the participant result based on
    the current state of the tennis match.

    Final:
        winner / loser

    Live:
        live

    Scheduled:
        scheduled
    """

    status = str(match_status or "").strip().lower()

    if status == "final":
        return "winner" if winner else "loser"

    if status == "live":
        return "live"

    return "scheduled"


def save_tennis_match(match_data):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        source_name = match_data.get("source_name")
        external_id = match_data.get("external_id")

        if not source_name or not external_id:
            return {
                "success": False,
                "message": "Missing source_name or external_id"
            }

        league_id = match_data.get("league_id")

        scheduled_at = match_data.get("scheduled_at")
        status = match_data.get("status")
        venue = match_data.get("venue")

        current_period = match_data.get("current_period")
        current_period_type = match_data.get(
            "current_period_type"
        )
        game_clock = match_data.get("game_clock")

        home_team_score = match_data.get(
            "home_team_score"
        )
        away_team_score = match_data.get(
            "away_team_score"
        )

        # --------------------------------------------------
        # 1. Find existing match
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM matches
            WHERE source_name = %s
              AND external_id = %s
            LIMIT 1;
            """,
            (
                source_name,
                str(external_id)
            )
        )

        existing_match = cursor.fetchone()

        if existing_match:
            match_id = existing_match[0]

            cursor.execute(
                """
                UPDATE matches
                SET
                    league_id = %s,
                    home_team_id = NULL,
                    away_team_id = NULL,
                    scheduled_at = %s,
                    status = %s,
                    venue = %s,
                    current_period = %s,
                    current_period_type = %s,
                    game_clock = %s,
                    home_team_score = %s,
                    away_team_score = %s
                WHERE id = %s;
                """,
                (
                    league_id,
                    scheduled_at,
                    status,
                    venue,
                    current_period,
                    current_period_type,
                    game_clock,
                    home_team_score,
                    away_team_score,
                    match_id
                )
            )

            match_action = "updated"

        else:
            cursor.execute(
                """
                INSERT INTO matches (
                    event_id,
                    league_id,
                    home_team_id,
                    away_team_id,
                    scheduled_at,
                    status,
                    venue,
                    current_period,
                    current_period_type,
                    game_clock,
                    external_id,
                    source_name,
                    home_team_score,
                    away_team_score
                )
                VALUES (
                    NULL,
                    %s,
                    NULL,
                    NULL,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id;
                """,
                (
                    league_id,
                    scheduled_at,
                    status,
                    venue,
                    current_period,
                    current_period_type,
                    game_clock,
                    str(external_id),
                    source_name,
                    home_team_score,
                    away_team_score
                )
            )

            match_id = cursor.fetchone()[0]

            match_action = "inserted"

        # --------------------------------------------------
        # 2. Save participants
        # --------------------------------------------------

        players = match_data.get("players") or []

        participant_results = []

        for player in players:

            player_id = player.get("player_id")
            participant_order = player.get(
                "participant_order"
            )

            winner = player.get("winner", False)

            if not player_id or not participant_order:
                continue

            result = get_participant_result(
                status,
                winner
            )

            # Check whether this participant
            # already exists for this match.
            cursor.execute(
                """
                SELECT id
                FROM match_participants
                WHERE match_id = %s
                  AND participant_order = %s
                LIMIT 1;
                """,
                (
                    match_id,
                    participant_order
                )
            )

            existing_participant = cursor.fetchone()

            if existing_participant:

                participant_id = existing_participant[0]

                cursor.execute(
                    """
                    UPDATE match_participants
                    SET
                        player_id = %s,
                        team_id = NULL,
                        result = %s
                    WHERE id = %s;
                    """,
                    (
                        player_id,
                        result,
                        participant_id
                    )
                )

                participant_action = "updated"

            else:

                cursor.execute(
                    """
                    INSERT INTO match_participants (
                        match_id,
                        player_id,
                        team_id,
                        participant_order,
                        result
                    )
                    VALUES (
                        %s,
                        %s,
                        NULL,
                        %s,
                        %s
                    )
                    RETURNING id;
                    """,
                    (
                        match_id,
                        player_id,
                        participant_order,
                        result
                    )
                )

                participant_id = cursor.fetchone()[0]

                participant_action = "inserted"

            participant_results.append({
                "id": participant_id,
                "player_id": player_id,
                "participant_order": participant_order,
                "result": result,
                "action": participant_action
            })

        # --------------------------------------------------
        # 3. Save tennis set scores
        # --------------------------------------------------

        set_scores = match_data.get("set_scores") or []

        set_score_results = []

        for set_score in set_scores:

            player_id = set_score.get("player_id")
            set_number = set_score.get("set_number")

            if not player_id or not set_number:
                continue

            games_won = set_score.get("games_won")

            tiebreak_points = set_score.get(
                "tiebreak_points"
            )

            is_winner = set_score.get(
                "is_winner"
            )

            cursor.execute(
                """
                SELECT id
                FROM tennis_set_scores
                WHERE match_id = %s
                  AND player_id = %s
                  AND set_number = %s
                LIMIT 1;
                """,
                (
                    match_id,
                    player_id,
                    set_number
                )
            )

            existing_set_score = cursor.fetchone()

            if existing_set_score:

                set_score_id = existing_set_score[0]

                cursor.execute(
                    """
                    UPDATE tennis_set_scores
                    SET
                        games_won = %s,
                        tiebreak_points = %s,
                        is_winner = %s
                    WHERE id = %s;
                    """,
                    (
                        games_won,
                        tiebreak_points,
                        is_winner,
                        set_score_id
                    )
                )

                set_action = "updated"

            else:

                cursor.execute(
                    """
                    INSERT INTO tennis_set_scores (
                        match_id,
                        player_id,
                        set_number,
                        games_won,
                        tiebreak_points,
                        is_winner
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id;
                    """,
                    (
                        match_id,
                        player_id,
                        set_number,
                        games_won,
                        tiebreak_points,
                        is_winner
                    )
                )

                set_score_id = cursor.fetchone()[0]

                set_action = "inserted"

            set_score_results.append({
                "id": set_score_id,
                "player_id": player_id,
                "set_number": set_number,
                "action": set_action
            })

        connection.commit()

        return {
            "success": True,
            "match_id": match_id,
            "match_action": match_action,
            "participants": participant_results,
            "set_scores": set_score_results
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def save_tennis_matches(processed_data):
    matches = processed_data.get("matches") or []

    results = []

    for match_data in matches:
        result = save_tennis_match(match_data)
        results.append(result)

    return {
        "success": True,
        "count": len(results),
        "results": results
    }