from datetime import datetime, timedelta, timezone
from typing import Any

from curl_cffi import requests

from app.database import get_connection


SOFASCORE_BASE_URL = (
    "https://www.sofascore.com/api/v1"
)

SOFASCORE_CACHE_SECONDS = 60

_sofascore_schedule_cache = {}


def get_tennis_matches(league_name="ATP"):
    """
    Return tennis matches for the requested tour.

    Existing ATP/WTA database matches are preserved.

    SofaScore finished matches already stored in the
    Atletiks tennis database are also included.

    SofaScore upcoming matches are fetched from the
    SofaScore tennis schedule and merged into the result.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                m.id,
                m.external_id,
                m.scheduled_at,
                m.status,
                m.venue,
                m.current_period,
                m.current_period_type,
                m.game_clock,
                m.home_team_score,
                m.away_team_score,
                l.name AS league_name
            FROM matches m
            JOIN leagues l
                ON l.id = m.league_id
            WHERE l.name = %s
            ORDER BY
                m.scheduled_at ASC NULLS LAST,
                m.id ASC;
            """,
            (league_name,),
        )

        match_rows = cursor.fetchall()

        matches = []

        for row in match_rows:
            match_id = row[0]

            cursor.execute(
                """
                SELECT
                    mp.player_id,
                    p.name AS player_name,
                    mp.participant_order,
                    mp.result
                FROM match_participants mp
                LEFT JOIN players p
                    ON p.id = mp.player_id
                WHERE mp.match_id = %s
                ORDER BY mp.participant_order;
                """,
                (match_id,),
            )

            participant_rows = cursor.fetchall()

            players = []

            for participant in participant_rows:
                players.append(
                    {
                        "player_id": participant[0],
                        "player_name": participant[1],
                        "participant_order": participant[2],
                        "result": participant[3],
                    }
                )

            cursor.execute(
                """
                SELECT
                    tss.player_id,
                    p.name AS player_name,
                    tss.set_number,
                    tss.games_won,
                    tss.tiebreak_points,
                    tss.is_winner
                FROM tennis_set_scores tss
                LEFT JOIN players p
                    ON p.id = tss.player_id
                WHERE tss.match_id = %s
                ORDER BY
                    tss.set_number,
                    tss.player_id;
                """,
                (match_id,),
            )

            set_rows = cursor.fetchall()

            set_scores = []

            for set_row in set_rows:
                set_scores.append(
                    {
                        "player_id": set_row[0],
                        "player_name": set_row[1],
                        "set_number": set_row[2],
                        "games_won": set_row[3],
                        "tiebreak_points": set_row[4],
                        "is_winner": set_row[5],
                    }
                )

            matches.append(
                {
                    "id": row[0],
                    "external_id": row[1],
                    "scheduled_at": row[2],
                    "status": row[3],
                    "venue": row[4],
                    "current_period": row[5],
                    "current_period_type": row[6],
                    "game_clock": row[7],
                    "player_one_score": row[8],
                    "player_two_score": row[9],
                    "league": row[10],
                    "players": players,
                    "set_scores": set_scores,
                    "source": "legacy",
                }
            )

        # ---------------------------------------------------------
        # Add finished SofaScore matches already stored in Atletiks
        # ---------------------------------------------------------

        sofascore_finished_matches = (
            get_stored_sofascore_matches(
                cursor,
                league_name,
                status_type="finished",
            )
        )

        existing_sofascore_ids = {
            match["id"]
            for match in matches
            if match.get("source") == "sofascore"
        }

        for match in sofascore_finished_matches:
            if match["id"] in existing_sofascore_ids:
                continue

            matches.append(match)

        # ---------------------------------------------------------
        # Add upcoming SofaScore matches
        # ---------------------------------------------------------

        sofascore_upcoming_matches = (
            get_sofascore_upcoming_matches(
                league_name
            )
        )

        existing_event_ids = {
            match.get("external_id")
            for match in matches
            if match.get("external_id") is not None
        }

        for match in sofascore_upcoming_matches:
            if (
                match.get("external_id")
                in existing_event_ids
            ):
                continue

            matches.append(match)

        return matches

    finally:
        cursor.close()
        connection.close()


def get_tennis_match(
    match_id,
    league_name="ATP",
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                m.id,
                m.external_id,
                m.scheduled_at,
                m.status,
                m.venue,
                m.current_period,
                m.current_period_type,
                m.game_clock,
                m.home_team_score,
                m.away_team_score,
                l.name AS league_name
            FROM matches m
            JOIN leagues l
                ON l.id = m.league_id
            WHERE m.id = %s
              AND l.name = %s
            LIMIT 1;
            """,
            (match_id, league_name),
        )

        row = cursor.fetchone()

        if not row:
            return None

        cursor.execute(
            """
            SELECT
                mp.player_id,
                p.name AS player_name,
                mp.participant_order,
                mp.result
            FROM match_participants mp
            LEFT JOIN players p
                ON p.id = mp.player_id
            WHERE mp.match_id = %s
            ORDER BY mp.participant_order;
            """,
            (match_id,),
        )

        participant_rows = cursor.fetchall()

        players = []

        for participant in participant_rows:
            players.append(
                {
                    "player_id": participant[0],
                    "player_name": participant[1],
                    "participant_order": participant[2],
                    "result": participant[3],
                }
            )

        cursor.execute(
            """
            SELECT
                tss.player_id,
                p.name AS player_name,
                tss.set_number,
                tss.games_won,
                tss.tiebreak_points,
                tss.is_winner
            FROM tennis_set_scores tss
            LEFT JOIN players p
                ON p.id = tss.player_id
            WHERE tss.match_id = %s
            ORDER BY
                tss.set_number,
                tss.player_id;
            """,
            (match_id,),
        )

        set_rows = cursor.fetchall()

        set_scores = []

        for set_row in set_rows:
            set_scores.append(
                {
                    "player_id": set_row[0],
                    "player_name": set_row[1],
                    "set_number": set_row[2],
                    "games_won": set_row[3],
                    "tiebreak_points": set_row[4],
                    "is_winner": set_row[5],
                }
            )

        return {
            "id": row[0],
            "external_id": row[1],
            "scheduled_at": row[2],
            "status": row[3],
            "venue": row[4],
            "current_period": row[5],
            "current_period_type": row[6],
            "game_clock": row[7],
            "player_one_score": row[8],
            "player_two_score": row[9],
            "league": row[10],
            "players": players,
            "set_scores": set_scores,
            "source": "legacy",
        }

    finally:
        cursor.close()
        connection.close()


def get_live_sofascore_tennis():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                tm.id,
                tm.sofascore_event_id,
                tm.custom_id,
                tm.slug,

                hp.sofascore_player_id,
                hp.name,
                hp.short_name,
                hp.ranking,
                hp.country,
                hp.country_code,

                ap.sofascore_player_id,
                ap.name,
                ap.short_name,
                ap.ranking,
                ap.country,
                ap.country_code,

                tt.sofascore_tournament_id,
                tt.name,
                tt.slug,
                tt.category,
                tt.ground_type,
                tt.tennis_points,

                tm.gender,

                tm.season_name,
                tm.season_year,

                tm.round_number,
                tm.round_name,
                tm.round_slug,

                tm.status_type,
                tm.status_description,
                tm.status_code,

                tm.start_time,

                tm.current_set_number,
                tm.current_set_home_games,
                tm.current_set_away_games,

                tm.home_sets,
                tm.away_sets,

                tm.current_home_points,
                tm.current_away_points,

                tm.first_to_serve,

                tm.ground_type,

                tm.is_live,
                tm.updated_at

            FROM tennis_matches tm

            JOIN tennis_players hp
                ON tm.home_player_id = hp.id

            JOIN tennis_players ap
                ON tm.away_player_id = ap.id

            JOIN tennis_tournaments tt
                ON tm.tournament_id = tt.id

            WHERE tm.is_live = TRUE

            ORDER BY
                tm.start_time ASC,
                tm.id ASC;
            """
        )

        rows = cursor.fetchall()

        matches = []

        for row in rows:
            match_id = row[0]

            cursor.execute(
                """
                SELECT
                    set_number,
                    home_score,
                    away_score
                FROM tennis_match_sets
                WHERE match_id = %s
                ORDER BY set_number;
                """,
                (match_id,),
            )

            set_rows = cursor.fetchall()

            sets = []

            for set_row in set_rows:
                sets.append(
                    {
                        "set_number": set_row[0],
                        "home_score": set_row[1],
                        "away_score": set_row[2],
                    }
                )

            matches.append(
                {
                    "id": row[0],
                    "sofascore_event_id": row[1],
                    "custom_id": row[2],
                    "slug": row[3],

                    "home_player": {
                        "id": row[4],
                        "name": row[5],
                        "short_name": row[6],
                        "ranking": row[7],
                        "country": row[8],
                        "country_code": row[9],
                    },

                    "away_player": {
                        "id": row[10],
                        "name": row[11],
                        "short_name": row[12],
                        "ranking": row[13],
                        "country": row[14],
                        "country_code": row[15],
                    },

                    "tournament": {
                        "id": row[16],
                        "name": row[17],
                        "slug": row[18],
                        "category": row[19],
                        "ground_type": row[20],
                        "tennis_points": row[21],
                    },

                    "gender": row[22],

                    "season": {
                        "name": row[23],
                        "year": row[24],
                    },

                    "round": {
                        "number": row[25],
                        "name": row[26],
                        "slug": row[27],
                    },

                    "status": {
                        "type": row[28],
                        "description": row[29],
                        "code": row[30],
                    },

                    "start_time": row[31],

                    "current_set": {
                        "number": row[32],
                        "home_games": row[33],
                        "away_games": row[34],
                    },

                    "score": {
                        "home_sets": row[35],
                        "away_sets": row[36],
                        "home_points": row[37],
                        "away_points": row[38],
                    },

                    "first_to_serve": row[39],
                    "ground_type": row[40],
                    "is_live": row[41],
                    "updated_at": row[42],

                    "sets": sets,
                }
            )

        return matches

    finally:
        cursor.close()
        connection.close()


def get_sofascore_tennis_match(match_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                tm.id,
                tm.sofascore_event_id,
                tm.custom_id,
                tm.slug,

                hp.sofascore_player_id,
                hp.name,
                hp.short_name,
                hp.ranking,
                hp.country,
                hp.country_code,

                ap.sofascore_player_id,
                ap.name,
                ap.short_name,
                ap.ranking,
                ap.country,
                ap.country_code,

                tt.sofascore_tournament_id,
                tt.name,
                tt.slug,
                tt.category,
                tt.ground_type,
                tt.tennis_points,

                tm.gender,

                tm.season_name,
                tm.season_year,

                tm.round_number,
                tm.round_name,
                tm.round_slug,

                tm.status_type,
                tm.status_description,
                tm.status_code,

                tm.start_time,

                tm.current_set_number,
                tm.current_set_home_games,
                tm.current_set_away_games,

                tm.home_sets,
                tm.away_sets,

                tm.current_home_points,
                tm.current_away_points,

                tm.first_to_serve,

                tm.ground_type,

                tm.is_live,
                tm.updated_at

            FROM tennis_matches tm

            JOIN tennis_players hp
                ON tm.home_player_id = hp.id

            JOIN tennis_players ap
                ON tm.away_player_id = ap.id

            JOIN tennis_tournaments tt
                ON tm.tournament_id = tt.id

            WHERE
    tm.id = %s
    OR tm.sofascore_event_id = %s

LIMIT 1;
            """,
            (match_id, match_id),

        )

        row = cursor.fetchone()

        if row is None:
            return None

        cursor.execute(
            """
            SELECT
                set_number,
                home_score,
                away_score
            FROM tennis_match_sets
            WHERE match_id = %s
            ORDER BY set_number;
            """,
            (match_id,),
        )

        set_rows = cursor.fetchall()

        sets = []

        for set_row in set_rows:
            sets.append(
                {
                    "set_number": set_row[0],
                    "home_score": set_row[1],
                    "away_score": set_row[2],
                }
            )

        cursor.execute(
            """
            SELECT
                recorded_at,
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
            LIMIT 100;
            """,
            (match_id,),
        )

        update_rows = cursor.fetchall()

        live_updates = []

        for update_row in update_rows:
            live_updates.append(
                {
                    "recorded_at": update_row[0],
                    "current_set_number": update_row[1],
                    "current_set": {
                        "home_games": update_row[2],
                        "away_games": update_row[3],
                    },
                    "score": {
                        "home_sets": update_row[4],
                        "away_sets": update_row[5],
                        "home_points": update_row[6],
                        "away_points": update_row[7],
                    },
                    "status": {
                        "type": update_row[8],
                        "description": update_row[9],
                    },
                    "first_to_serve": update_row[10],
                }
            )

        return {
            "id": row[0],
            "sofascore_event_id": row[1],
            "custom_id": row[2],
            "slug": row[3],

            "home_player": {
                "id": row[4],
                "name": row[5],
                "short_name": row[6],
                "ranking": row[7],
                "country": row[8],
                "country_code": row[9],
            },

            "away_player": {
                "id": row[10],
                "name": row[11],
                "short_name": row[12],
                "ranking": row[13],
                "country": row[14],
                "country_code": row[15],
            },

            "tournament": {
                "id": row[16],
                "name": row[17],
                "slug": row[18],
                "category": row[19],
                "ground_type": row[20],
                "tennis_points": row[21],
            },

            "gender": row[22],

            "season": {
                "name": row[23],
                "year": row[24],
            },

            "round": {
                "number": row[25],
                "name": row[26],
                "slug": row[27],
            },

            "status": {
                "type": row[28],
                "description": row[29],
                "code": row[30],
            },

            "start_time": row[31],

            "current_set": {
                "number": row[32],
                "home_games": row[33],
                "away_games": row[34],
            },

            "score": {
                "home_sets": row[35],
                "away_sets": row[36],
                "home_points": row[37],
                "away_points": row[38],
            },

            "first_to_serve": row[39],
            "ground_type": row[40],
            "is_live": row[41],
            "updated_at": row[42],

            "sets": sets,
            "live_updates": live_updates,
        }

    finally:
        cursor.close()
        connection.close()


# ================================================================
# SofaScore calendar helpers
# ================================================================


def create_sofascore_session():
    return requests.Session(
        impersonate="chrome"
    )


def is_matching_tour(
    event: dict[str, Any],
    league_name: str,
) -> bool:
    """
    Match SofaScore tennis events to the Atletiks
    ATP or WTA tab.

    ATP = men's professional singles.
    WTA = women's professional singles.
    """

    event_filters = (
        event.get("eventFilters") or {}
    )

    categories = (
        event_filters.get("category") or []
    )

    levels = (
        event_filters.get("level") or []
    )

    genders = (
        event_filters.get("gender") or []
    )

    if "singles" not in categories:
        return False

    if "pro" not in levels:
        return False

    if league_name.upper() == "ATP":
        return "M" in genders

    if league_name.upper() == "WTA":
        return "W" in genders

    return False


def has_valid_sofascore_players(
    event: dict[str, Any],
) -> bool:
    home_player = event.get("homeTeam") or {}
    away_player = event.get("awayTeam") or {}

    home_name = (
        home_player.get("name")
        or ""
    ).strip()

    away_name = (
        away_player.get("name")
        or ""
    ).strip()

    if not home_name or not away_name:
        return False

    invalid_names = {
        "tbd",
        "to be determined",
        "unknown",
    }

    if (
        home_name.lower() in invalid_names
        or away_name.lower() in invalid_names
    ):
        return False

    return True


def get_sofascore_scheduled_events(
    date_value: str,
) -> list[dict[str, Any]]:
    """
    Fetch SofaScore tennis matches for one date.

    SofaScore's tennis schedule has changed over time,
    so we try the current scheduled-events endpoint first
    and then the alternate scheduled-tournaments endpoint.

    Results are cached briefly so the frontend's polling
    does not repeatedly hammer SofaScore.
    """

    cache_key = date_value

    cached = _sofascore_schedule_cache.get(
        cache_key
    )

    if cached:
        cached_at, cached_events = cached

        age = (
            datetime.now(timezone.utc)
            - cached_at
        ).total_seconds()

        if age < SOFASCORE_CACHE_SECONDS:
            return cached_events

    session = create_sofascore_session()

    urls = [
        (
            f"{SOFASCORE_BASE_URL}"
            f"/sport/tennis/"
            f"scheduled-events/"
            f"{date_value}"
        ),
        (
            f"{SOFASCORE_BASE_URL}"
            f"/sport/tennis/"
            f"scheduled-tournaments/"
            f"{date_value}/page/1"
        ),
    ]

    for url in urls:
        try:
            response = session.get(
                url,
                timeout=20,
            )

            if response.status_code != 200:
                continue

            data = response.json()

            events = data.get("events")

            if isinstance(events, list):
                _sofascore_schedule_cache[
                    cache_key
                ] = (
                    datetime.now(timezone.utc),
                    events,
                )

                return events

            # Some SofaScore tennis schedule responses
            # may provide tournaments instead of events.
            tournaments = data.get(
                "scheduledTournaments"
            )

            if isinstance(tournaments, list):
                events = []

                for tournament in tournaments:
                    tournament_events = (
                        tournament.get("events")
                        or []
                    )

                    if isinstance(
                        tournament_events,
                        list,
                    ):
                        events.extend(
                            tournament_events
                        )

                _sofascore_schedule_cache[
                    cache_key
                ] = (
                    datetime.now(timezone.utc),
                    events,
                )

                return events

        except Exception as error:
            print(
                f"SofaScore schedule request failed "
                f"for {date_value}: {error}"
            )

    _sofascore_schedule_cache[
        cache_key
    ] = (
        datetime.now(timezone.utc),
        [],
    )

    return []


def normalize_sofascore_calendar_match(
    event: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Convert a SofaScore calendar event into the
    existing Atletiks tennis card structure.
    """

    if not has_valid_sofascore_players(event):
        return None

    tournament = (
        event.get("tournament") or {}
    )

    unique_tournament = (
        tournament.get(
            "uniqueTournament"
        )
        or {}
    )

    category = (
        tournament.get("category") or {}
    )

    home_player = (
        event.get("homeTeam") or {}
    )

    away_player = (
        event.get("awayTeam") or {}
    )

    status = event.get("status") or {}

    home_score = (
        event.get("homeScore") or {}
    )

    away_score = (
        event.get("awayScore") or {}
    )

    status_type = (
        status.get("type")
        or ""
    )

    if status_type == "finished":
        card_status = "COMPLETED"
    elif status_type == "inprogress":
        card_status = "LIVE"
    else:
        card_status = "SCHEDULED"

    home_sets = home_score.get(
        "current"
    )

    away_sets = away_score.get(
        "current"
    )

    try:
        home_sets = (
            int(home_sets)
            if home_sets is not None
            else 0
        )
    except (TypeError, ValueError):
        home_sets = 0

    try:
        away_sets = (
            int(away_sets)
            if away_sets is not None
            else 0
        )
    except (TypeError, ValueError):
        away_sets = 0

    start_timestamp = (
        event.get("startTimestamp")
    )

    scheduled_at = None

    if start_timestamp is not None:
        try:
            scheduled_at = (
                datetime.fromtimestamp(
                    int(start_timestamp),
                    tz=timezone.utc,
                ).isoformat()
            )
        except (
            TypeError,
            ValueError,
            OSError,
        ):
            scheduled_at = None

    return {
        "id": (
            f"sofascore-"
            f"{event.get('id')}"
        ),

        "external_id": event.get("id"),

        "scheduled_at": scheduled_at,

        "status": card_status,

        "venue": (
            event.get("groundType")
            or unique_tournament.get(
                "groundType"
            )
            or "Tennis"
        ),

        "current_period": (
            event.get("lastPeriod")
        ),

        "current_period_type": (
            event.get("lastPeriod")
        ),

        "game_clock": None,

        "home_team_score": home_sets,

        "away_team_score": away_sets,

        "player_one_score": home_sets,

        "player_two_score": away_sets,

        "league": (
            category.get("name")
            or unique_tournament.get(
                "name"
            )
            or tournament.get("name")
            or "Tennis"
        ),

        "players": [
            {
                "player_id":
                    home_player.get("id"),
                "player_name":
                    home_player.get("name"),
                "participant_order": 1,
                "result": (
                    "winner"
                    if event.get(
                        "winnerCode"
                    ) == 1
                    else None
                ),
            },
            {
                "player_id":
                    away_player.get("id"),
                "player_name":
                    away_player.get("name"),
                "participant_order": 2,
                "result": (
                    "winner"
                    if event.get(
                        "winnerCode"
                    ) == 2
                    else None
                ),
            },
        ],

        "set_scores": [],

        "source": "sofascore",

        "sofascore_event": event,
    }


def get_sofascore_upcoming_matches(
    league_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch upcoming professional singles matches
    for the selected ATP/WTA tab.

    We look across the current day and the next
    seven calendar days.
    """

    results = []

    today = datetime.now(
        timezone.utc
    ).date()

    for offset in range(0, 8):
        date_value = (
            today + timedelta(days=offset)
        ).isoformat()

        events = (
            get_sofascore_scheduled_events(
                date_value
            )
        )

        for event in events:

            if not is_matching_tour(
                event,
                league_name,
            ):
                continue

            if not has_valid_sofascore_players(
                event
            ):
                continue

            status = (
                event.get("status") or {}
            )

            status_type = (
                status.get("type")
                or ""
            )

            if status_type == "finished":
                continue

            if status_type == "canceled":
                continue

            normalized = (
                normalize_sofascore_calendar_match(
                    event
                )
            )

            if normalized is None:
                continue

            results.append(normalized)

    results.sort(
        key=lambda match: (
            match.get("scheduled_at")
            or ""
        )
    )

    return results


def get_stored_sofascore_matches(
    cursor,
    league_name: str,
    status_type: str,
) -> list[dict[str, Any]]:
    """
    Read SofaScore matches already stored in
    the Atletiks database.

    Used mainly for finished matches such as
    Matic Hribar vs Leon Giorgi Sarishvili.
    """

    expected_gender = {
        "ATP": "M",
        "WTA": "W",
    }.get(
        league_name.upper()
    )

    if expected_gender is None:
        return []

    cursor.execute(
        """
        SELECT
            tm.id,
            tm.sofascore_event_id,
            tm.custom_id,
            tm.slug,

            hp.sofascore_player_id,
            hp.name,
            hp.short_name,
            hp.ranking,
            hp.country,
            hp.country_code,

            ap.sofascore_player_id,
            ap.name,
            ap.short_name,
            ap.ranking,
            ap.country,
            ap.country_code,

            tt.sofascore_tournament_id,
            tt.name,
            tt.slug,
            tt.category,
            tt.ground_type,
            tt.tennis_points,

            tm.gender,

            tm.season_name,
            tm.season_year,

            tm.round_number,
            tm.round_name,
            tm.round_slug,

            tm.status_type,
            tm.status_description,
            tm.status_code,

            tm.start_time,

            tm.current_set_number,
            tm.current_set_home_games,
            tm.current_set_away_games,

            tm.home_sets,
            tm.away_sets,

            tm.current_home_points,
            tm.current_away_points,

            tm.first_to_serve,

            tm.ground_type,

            tm.is_live,
            tm.updated_at

        FROM tennis_matches tm

        JOIN tennis_players hp
            ON tm.home_player_id = hp.id

        JOIN tennis_players ap
            ON tm.away_player_id = ap.id

        JOIN tennis_tournaments tt
            ON tm.tournament_id = tt.id

        WHERE tm.status_type = %s
          AND tm.gender = %s
          AND tm.is_live = FALSE

        ORDER BY
            tm.start_time DESC,
            tm.id DESC;
        """,
        (
            status_type,
            expected_gender,
        ),
    )

    rows = cursor.fetchall()

    matches = []

    for row in rows:
        match_id = row[0]

        cursor.execute(
            """
            SELECT
                set_number,
                home_score,
                away_score
            FROM tennis_match_sets
            WHERE match_id = %s
            ORDER BY set_number;
            """,
            (match_id,),
        )

        set_rows = cursor.fetchall()

        sets = []

        for set_row in set_rows:
            sets.append(
                {
                    "set_number": set_row[0],
                    "home_score": set_row[1],
                    "away_score": set_row[2],
                }
            )

        home_result = None
        away_result = None

        if row[35] is not None:
            try:
                if int(row[35]) > int(row[36]):
                    home_result = "winner"
                    away_result = "loser"
                elif int(row[36]) > int(row[35]):
                    home_result = "loser"
                    away_result = "winner"
            except (
                TypeError,
                ValueError,
            ):
                pass

        matches.append(
            {
                "id": (
                    f"sofascore-db-"
                    f"{row[0]}"
                ),

                "external_id": row[1],

                "scheduled_at": row[31],

                "status": "COMPLETED",

                "venue": (
                    row[40]
                    or row[20]
                    or "Tennis"
                ),

                "current_period": (
                    len(sets)
                    if sets
                    else None
                ),

                "current_period_type": None,

                "game_clock": None,

                "player_one_score": (
                    row[35] or 0
                ),

                "player_two_score": (
                    row[36] or 0
                ),

                "league": (
                    row[19]
                    or row[17]
                    or "Tennis"
                ),

                "players": [
                    {
                        "player_id": row[4],
                        "player_name": row[5],
                        "participant_order": 1,
                        "result": home_result,
                    },
                    {
                        "player_id": row[10],
                        "player_name": row[11],
                        "participant_order": 2,
                        "result": away_result,
                    },
                ],

                "set_scores": sets,

                "source": "sofascore",

                "sofascore_event_id": row[1],

                "sofascore": {
                    "id": row[1],
                    "gender": row[22],
                    "season": {
                        "name": row[23],
                        "year": row[24],
                    },
                    "round": {
                        "number": row[25],
                        "name": row[26],
                        "slug": row[27],
                    },
                    "tournament": {
                        "id": row[16],
                        "name": row[17],
                        "slug": row[18],
                        "category": row[19],
                        "ground_type": row[20],
                        "tennis_points": row[21],
                    },
                },
            }
        )

    return matches