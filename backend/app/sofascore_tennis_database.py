from typing import Any

from app.database import get_connection
from app.sofascore_tennis_processor import (
    get_live_professional_singles,
    fetch_tennis_event,
    normalize_event,
)


def upsert_player(
    cursor,
    player: dict[str, Any],
) -> int:
    """
    Insert a tennis player if they do not exist.

    If the player already exists, update their information.

    Returns the PostgreSQL player ID.
    """

    sofascore_player_id = player.get("id")

    if sofascore_player_id is None:
        raise ValueError(
            "Player is missing a SofaScore player ID."
        )

    cursor.execute(
        """
        INSERT INTO tennis_players (
            sofascore_player_id,
            name,
            short_name,
            gender,
            ranking,
            country,
            country_code
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (sofascore_player_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            short_name = EXCLUDED.short_name,
            gender = EXCLUDED.gender,
            ranking = EXCLUDED.ranking,
            country = EXCLUDED.country,
            country_code = EXCLUDED.country_code,
            updated_at = NOW()
        RETURNING id;
        """,
        (
            sofascore_player_id,
            player.get("name"),
            player.get("short_name"),
            player.get("gender"),
            player.get("ranking"),
            player.get("country"),
            player.get("country_code"),
        ),
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "Unable to retrieve tennis player ID."
        )

    return row[0]


def upsert_tournament(
    cursor,
    tournament: dict[str, Any],
) -> int:
    """
    Insert a tennis tournament if it does not exist.

    If the tournament already exists, update its information.

    Returns the PostgreSQL tournament ID.
    """

    sofascore_tournament_id = tournament.get("id")

    if sofascore_tournament_id is None:
        raise ValueError(
            "Tournament is missing a SofaScore tournament ID."
        )

    cursor.execute(
        """
        INSERT INTO tennis_tournaments (
            sofascore_tournament_id,
            name,
            slug,
            category,
            ground_type,
            tennis_points
        )
        VALUES (
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (sofascore_tournament_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            slug = EXCLUDED.slug,
            category = EXCLUDED.category,
            ground_type = EXCLUDED.ground_type,
            tennis_points = EXCLUDED.tennis_points,
            updated_at = NOW()
        RETURNING id;
        """,
        (
            sofascore_tournament_id,
            tournament.get("name"),
            tournament.get("slug"),
            tournament.get("category"),
            tournament.get("ground_type"),
            tournament.get("tennis_points"),
        ),
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "Unable to retrieve tennis tournament ID."
        )

    return row[0]

def upsert_match(
    cursor,
    match: dict[str, Any],
    tournament_id: int,
    home_player_id: int,
    away_player_id: int,
) -> int:
    """
    Insert or update a tennis match.

    Returns the PostgreSQL match ID.
    """

    status = match["status"]
    current_set = match["current_set"]
    score = match["score"]
    current_points = score["current_game_points"]

    values = (
        match["sofascore_event_id"],
        match["custom_id"],
        match["slug"],
        tournament_id,
        home_player_id,
        away_player_id,
        match["gender"],
        match["season"]["name"],
        match["season"]["year"],
        match["round"]["number"],
        match["round"]["name"],
        match["round"]["slug"],
        status["type"],
        status["description"],
        status["code"],
        match["start_time"],
        current_set["number"],
        current_set["home_games"],
        current_set["away_games"],
        score["home_sets"],
        score["away_sets"],
        current_points["home"],
        current_points["away"],
        match["first_to_serve"],
        match["ground_type"],
        status["type"] == "inprogress",
    )

    cursor.execute(
        """
        INSERT INTO tennis_matches (
            sofascore_event_id,
            custom_id,
            slug,
            tournament_id,
            home_player_id,
            away_player_id,
            gender,
            season_name,
            season_year,
            round_number,
            round_name,
            round_slug,
            status_type,
            status_description,
            status_code,
            start_time,
            current_set_number,
            current_set_home_games,
            current_set_away_games,
            home_sets,
            away_sets,
            current_home_points,
            current_away_points,
            first_to_serve,
            ground_type,
            is_live
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
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
        ON CONFLICT (sofascore_event_id)
        DO UPDATE SET
            custom_id = EXCLUDED.custom_id,
            slug = EXCLUDED.slug,
            tournament_id = EXCLUDED.tournament_id,
            home_player_id = EXCLUDED.home_player_id,
            away_player_id = EXCLUDED.away_player_id,
            gender = EXCLUDED.gender,
            season_name = EXCLUDED.season_name,
            season_year = EXCLUDED.season_year,
            round_number = EXCLUDED.round_number,
            round_name = EXCLUDED.round_name,
            round_slug = EXCLUDED.round_slug,
            status_type = EXCLUDED.status_type,
            status_description = EXCLUDED.status_description,
            status_code = EXCLUDED.status_code,
            start_time = EXCLUDED.start_time,
            current_set_number = EXCLUDED.current_set_number,
            current_set_home_games = EXCLUDED.current_set_home_games,
            current_set_away_games = EXCLUDED.current_set_away_games,
            home_sets = EXCLUDED.home_sets,
            away_sets = EXCLUDED.away_sets,
            current_home_points = EXCLUDED.current_home_points,
            current_away_points = EXCLUDED.current_away_points,
            first_to_serve = EXCLUDED.first_to_serve,
            ground_type = EXCLUDED.ground_type,
            is_live = EXCLUDED.is_live,
            updated_at = NOW()
        RETURNING id;
        """,
        values,
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "Unable to retrieve tennis match ID."
        )

    return row[0]

def replace_match_sets(
    cursor,
    match_id: int,
    sets: list[dict[str, Any]],
) -> None:
    """
    Replace the stored set scores for a match.

    The current SofaScore result is treated as the latest
    source of truth for the match's set scores.
    """

    cursor.execute(
        """
        DELETE FROM tennis_match_sets
        WHERE match_id = %s;
        """,
        (match_id,),
    )

    for tennis_set in sets:
        cursor.execute(
            """
            INSERT INTO tennis_match_sets (
                match_id,
                set_number,
                home_score,
                away_score
            )
            VALUES (
                %s, %s, %s, %s
            );
            """,
            (
                match_id,
                tennis_set["set_number"],
                tennis_set["home"],
                tennis_set["away"],
            ),
        )


def insert_live_update(
    cursor,
    match_id: int,
    match: dict[str, Any],
) -> None:
    """
    Store a live state only when it differs from the
    most recently stored live state.
    """

    status = match["status"]
    current_set = match["current_set"]
    score = match["score"]

    current_points = score["current_game_points"]

    if status["type"] != "inprogress":
        return

    current_state = (
        current_set["number"],
        current_set["home_games"],
        current_set["away_games"],
        score["home_sets"],
        score["away_sets"],
        current_points["home"],
        current_points["away"],
        status["type"],
        status["description"],
        match["first_to_serve"],
    )

    cursor.execute(
        """
        SELECT
            current_set_number,
            current_set_home_games,
            current_set_away_games,
            home_sets,
            away_sets,
            current_home_points,
            current_away_points,
            status_type,
            status_description,
            first_to_serve
        FROM tennis_match_live_updates
        WHERE match_id = %s
        ORDER BY recorded_at DESC
        LIMIT 1;
        """,
        (match_id,),
    )

    previous_row = cursor.fetchone()

    if previous_row is not None:
        previous_state = tuple(previous_row)

        if previous_state == current_state:
            return

    cursor.execute(
        """
        INSERT INTO tennis_match_live_updates (
            match_id,
            current_set_number,
            current_set_home_games,
            current_set_away_games,
            home_sets,
            away_sets,
            current_home_points,
            current_away_points,
            status_type,
            status_description,
            first_to_serve
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        );
        """,
        (
            match_id,
            current_set["number"],
            current_set["home_games"],
            current_set["away_games"],
            score["home_sets"],
            score["away_sets"],
            current_points["home"],
            current_points["away"],
            status["type"],
            status["description"],
            match["first_to_serve"],
        ),
    )


def process_live_tennis() -> int:
    """
    Fetch live SofaScore tennis matches and store them
    in PostgreSQL.

    Also checks previously-live matches individually
    so finished matches receive their final score.

    Returns the number of matches processed.
    """

    live_matches = get_live_professional_singles()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        processed = 0
        finished_processed = 0

        # ---------------------------------------------------------
        # 1. Process currently live matches
        # ---------------------------------------------------------

        for match in live_matches:
            home_player_id = upsert_player(
                cursor,
                match["home_player"],
            )

            away_player_id = upsert_player(
                cursor,
                match["away_player"],
            )

            tournament_id = upsert_tournament(
                cursor,
                match["tournament"],
            )

            match_id = upsert_match(
                cursor,
                match,
                tournament_id,
                home_player_id,
                away_player_id,
            )

            replace_match_sets(
                cursor,
                match_id,
                match["score"]["sets"],
            )

            insert_live_update(
                cursor,
                match_id,
                match,
            )

            processed += 1

        # ---------------------------------------------------------
        # 2. Find matches that were previously live
        # ---------------------------------------------------------
        #
        # These matches may have disappeared from SofaScore's
        # /events/live endpoint because they just finished.
        #
        # We retrieve their SofaScore event IDs and check each
        # individual event endpoint.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                sofascore_event_id
            FROM tennis_matches
            WHERE is_live = TRUE
            ORDER BY updated_at DESC;
            """
        )

        previous_live_matches = cursor.fetchall()

        for database_match_id, sofascore_event_id in (
            previous_live_matches
        ):
            # If the match is still present in the live feed,
            # it was already processed above.
            #
            # We still allow the event check because this handles
            # a match that has just transitioned to finished.
            try:
                event = fetch_tennis_event(
                    sofascore_event_id
                )

            except Exception as event_error:
                print(
                    f"Unable to refresh SofaScore event "
                    f"{sofascore_event_id}: "
                    f"{event_error}"
                )

                continue

            status = event.get("status") or {}

            if status.get("type") != "finished":
                continue

            # -----------------------------------------------------
            # 3. Normalize the finished SofaScore event
            # -----------------------------------------------------

            finished_match = normalize_event(
                event
            )

            home_player_id = upsert_player(
                cursor,
                finished_match["home_player"],
            )

            away_player_id = upsert_player(
                cursor,
                finished_match["away_player"],
            )

            tournament_id = upsert_tournament(
                cursor,
                finished_match["tournament"],
            )

            updated_match_id = upsert_match(
                cursor,
                finished_match,
                tournament_id,
                home_player_id,
                away_player_id,
            )

            # -----------------------------------------------------
            # 4. Replace the set scores with the final result
            # -----------------------------------------------------

            replace_match_sets(
                cursor,
                updated_match_id,
                finished_match["score"]["sets"],
            )

            finished_processed += 1

            print(
                f"Finished tennis match updated: "
                f"{finished_match['home_player']['name']} "
                f"{finished_match['score']['home_sets']}"
                f"-"
                f"{finished_match['score']['away_sets']} "
                f"{finished_match['away_player']['name']}"
            )

        # ---------------------------------------------------------
        # 5. Commit everything
        # ---------------------------------------------------------

        connection.commit()

        total_processed = (
            processed +
            finished_processed
        )

        print(
            f"Successfully processed "
            f"{processed} live tennis match(es) "
            f"and "
            f"{finished_processed} finished tennis "
            f"match(es)."
        )

        return total_processed

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def main():
    process_live_tennis()


if __name__ == "__main__":
    main()