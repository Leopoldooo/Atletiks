from app.database import get_connection


def get_or_create_player(player_data):
    external_id = player_data.get("external_id")
    name = player_data.get("name")

    if not external_id or not name:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM players
            WHERE source_name = %s
              AND external_id = %s
            LIMIT 1;
            """,
            ("espn", str(external_id))
        )

        result = cursor.fetchone()

        if result:
            player_id = result[0]

            cursor.execute(
                """
                UPDATE players
                SET
                    name = %s
                WHERE id = %s;
                """,
                (
                    name,
                    player_id
                )
            )

            connection.commit()

            return player_id

        name_parts = name.split(" ", 1)

        first_name = name_parts[0]
        last_name = (
            name_parts[1]
            if len(name_parts) > 1
            else None
        )

        cursor.execute(
            """
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
                    WHERE name = 'Tennis'
                    LIMIT 1
                ),
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id;
            """,
            (
                name,
                first_name,
                last_name,
                str(external_id),
                "espn"
            )
        )

        player_id = cursor.fetchone()[0]

        connection.commit()

        return player_id

    finally:
        cursor.close()
        connection.close()


def get_tennis_league_id(league_name):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM leagues
            WHERE name = %s
            LIMIT 1;
            """,
            (league_name,)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def get_status(competition):
    status = competition.get("status") or {}
    status_type = status.get("type") or {}

    state = status_type.get("state")

    if state == "pre":
        return "Scheduled"

    if state == "in":
        return "Live"

    if state == "post":
        return "Final"

    description = status_type.get("description")

    if description:
        return description

    return "Scheduled"


def get_current_period(competition):
    status = competition.get("status") or {}

    period = status.get("period")

    if period is None:
        return None

    try:
        return int(period)
    except (ValueError, TypeError):
        return None


def get_current_period_type(competition):
    return "Set"


def get_game_clock(competition):
    status = competition.get("status") or {}

    clock = status.get("displayClock")

    if clock:
        return str(clock)

    return None


def get_sets_won(competitor):
    linescores = competitor.get("linescores") or []

    sets_won = 0

    for line in linescores:
        if line.get("winner") is True:
            sets_won += 1

    return sets_won


def get_integer_value(value, default=0):
    if value is None:
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def process_tennis_competition(
    event,
    competition,
    league_name
):
    competitors = competition.get("competitors") or []

    if len(competitors) < 2:
        return None

    competitors = sorted(
        competitors,
        key=lambda item: item.get("order", 99)
    )

    player_one = competitors[0]
    player_two = competitors[1]

    athlete_one = player_one.get("athlete") or {}
    athlete_two = player_two.get("athlete") or {}

    player_one_external_id = (
        athlete_one.get("id")
        or player_one.get("id")
    )

    player_two_external_id = (
        athlete_two.get("id")
        or player_two.get("id")
    )

    player_one_name = (
        athlete_one.get("displayName")
        or athlete_one.get("fullName")
        or athlete_one.get("shortName")
    )

    player_two_name = (
        athlete_two.get("displayName")
        or athlete_two.get("fullName")
        or athlete_two.get("shortName")
    )

    player_one_data = {
        "external_id": player_one_external_id,
        "name": player_one_name
    }

    player_two_data = {
        "external_id": player_two_external_id,
        "name": player_two_name
    }

    player_one_id = get_or_create_player(
        player_one_data
    )

    player_two_id = get_or_create_player(
        player_two_data
    )

    if player_one_id is None or player_two_id is None:
        return None

    competition_id = competition.get("id")

    if not competition_id:
        return None

    scheduled_at = (
        competition.get("startDate")
        or competition.get("date")
        or event.get("date")
    )

    status = get_status(competition)

    venue = competition.get("venue") or {}

    venue_name = venue.get("fullName")

    court = venue.get("court")

    if court:
        if venue_name:
            venue_name = f"{venue_name} - {court}"
        else:
            venue_name = court

    set_scores = []

    player_one_linescores = (
        player_one.get("linescores") or []
    )

    player_two_linescores = (
        player_two.get("linescores") or []
    )

    max_sets = max(
        len(player_one_linescores),
        len(player_two_linescores)
    )

    for index in range(max_sets):
        set_number = index + 1

        player_one_set = (
            player_one_linescores[index]
            if index < len(player_one_linescores)
            else {}
        )

        player_two_set = (
            player_two_linescores[index]
            if index < len(player_two_linescores)
            else {}
        )

        player_one_score = get_integer_value(
            player_one_set.get("value")
        )

        player_two_score = get_integer_value(
            player_two_set.get("value")
        )

        player_one_tiebreak = (
            player_one_set.get("tiebreak")
        )

        player_two_tiebreak = (
            player_two_set.get("tiebreak")
        )

        set_scores.append({
            "player_id": player_one_id,
            "participant_order": 1,
            "set_number": set_number,
            "games_won": player_one_score,
            "tiebreak_points": (
                get_integer_value(
                    player_one_tiebreak,
                    None
                )
                if player_one_tiebreak is not None
                else None
            ),
            "is_winner": bool(
                player_one_set.get(
                    "winner",
                    False
                )
            )
        })

        set_scores.append({
            "player_id": player_two_id,
            "participant_order": 2,
            "set_number": set_number,
            "games_won": player_two_score,
            "tiebreak_points": (
                get_integer_value(
                    player_two_tiebreak,
                    None
                )
                if player_two_tiebreak is not None
                else None
            ),
            "is_winner": bool(
                player_two_set.get(
                    "winner",
                    False
                )
            )
        })

    tournament_name = (
        event.get("name")
        or event.get("shortName")
    )

    event_id = event.get("id")

    tournament_id = None

    if event_id:
        event_id_text = str(event_id)

        if "-" in event_id_text:
            tournament_id = event_id_text.split("-", 1)[0]
        else:
            tournament_id = event_id_text

    round_data = competition.get("round") or {}

    round_name = round_data.get("displayName")

    competition_type = competition.get("type") or {}

    match_type = competition_type.get("text")

    return {
        "source_name": "espn",
        "external_id": str(competition_id),
        "league_name": league_name,
        "league_id": get_tennis_league_id(
            league_name
        ),
        "scheduled_at": scheduled_at,
        "status": status,
        "venue": venue_name,
        "current_period": get_current_period(
            competition
        ),
        "current_period_type": get_current_period_type(
            competition
        ),
        "game_clock": get_game_clock(
            competition
        ),
        "home_team_score": get_sets_won(
            player_one
        ),
        "away_team_score": get_sets_won(
            player_two
        ),
        "tournament_id": tournament_id,
        "tournament_name": tournament_name,
        "round": round_name,
        "match_type": match_type,
        "players": [
            {
                "player_id": player_one_id,
                "external_id": player_one_external_id,
                "name": player_one_name,
                "participant_order": 1,
                "winner": bool(
                    player_one.get(
                        "winner",
                        False
                    )
                )
            },
            {
                "player_id": player_two_id,
                "external_id": player_two_external_id,
                "name": player_two_name,
                "participant_order": 2,
                "winner": bool(
                    player_two.get(
                        "winner",
                        False
                    )
                )
            }
        ],
        "set_scores": set_scores
    }


def get_event_list(response_data):
    """
    ESPN normally returns:

    {
        "events": [
            ...
        ]
    }

    This function also handles cases where n8n
    passes the events array directly.
    """

    if isinstance(response_data, list):
        return response_data

    if not isinstance(response_data, dict):
        return []

    events = response_data.get("events")

    if isinstance(events, list):
        return events

    return []


def get_singles_competitions(event, league_name):
    """
    Extract the correct singles competitions from
    ESPN's tournament grouping structure.

    ATP uses:
        mens-singles

    WTA uses:
        womens-singles
    """

    competitions = []

    groupings = event.get("groupings") or []

    league_name = str(
        league_name or ""
    ).upper()

    if league_name == "WTA":
        target_slug = "womens-singles"
        target_text = "women's singles"
    else:
        target_slug = "mens-singles"
        target_text = "men's singles"

    for grouping_data in groupings:
        grouping = grouping_data.get("grouping") or {}

        grouping_slug = grouping.get("slug")

        grouping_text = (
            grouping.get("displayName")
            or grouping.get("text")
            or ""
        )

        is_target_singles = (
            grouping_slug == target_slug
            or grouping_text.lower() == target_text
        )

        if not is_target_singles:
            continue

        grouping_competitions = (
            grouping_data.get("competitions") or []
        )

        for competition in grouping_competitions:
            competitions.append(competition)

    return competitions


def detect_league(response_data, requested_league=None):
    """
    Determine whether the ESPN scoreboard is ATP or WTA.

    The n8n workflows currently send the ESPN response
    directly as {{ $json }}, so we cannot rely on an
    extra wrapper field being supplied by n8n.

    We first use the requested league when supplied.

    Otherwise, we inspect the ESPN response for the
    league name/abbreviation.
    """

    if requested_league:
        requested = str(
            requested_league
        ).strip().upper()

        if requested in ["ATP", "WTA"]:
            return requested

    if isinstance(response_data, dict):
        league_data = response_data.get("leagues")

        if isinstance(league_data, list):
            for league in league_data:
                league_name = str(
                    league.get("name") or ""
                ).upper()

                league_abbreviation = str(
                    league.get("abbreviation") or ""
                ).upper()

                if league_name == "WTA":
                    return "WTA"

                if league_abbreviation == "WTA":
                    return "WTA"

                if league_name == "ATP":
                    return "ATP"

                if league_abbreviation == "ATP":
                    return "ATP"

    return None


def process_tennis_scoreboard(
    response_data,
    league_name=None
):
    detected_league = detect_league(
        response_data,
        league_name
    )

    if detected_league is None:
        return {
            "league": None,
            "count": 0,
            "matches": [],
            "error": "Unable to determine ATP or WTA league"
        }

    events = get_event_list(response_data)

    matches = []

    for event in events:

        competitions = get_singles_competitions(
            event,
            detected_league
        )

        for competition in competitions:

            processed_match = process_tennis_competition(
                event,
                competition,
                detected_league
            )

            if processed_match:
                matches.append(
                    processed_match
                )

    return {
        "league": detected_league,
        "count": len(matches),
        "matches": matches
    }