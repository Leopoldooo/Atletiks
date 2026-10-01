from datetime import datetime, timezone
from typing import Any

from curl_cffi import requests


BASE_URL = "https://www.sofascore.com/api/v1"


def create_session():
    """
    Create a SofaScore HTTP session using Chrome TLS impersonation.
    """
    return requests.Session(impersonate="chrome")


def fetch_live_tennis_events() -> list[dict[str, Any]]:
    """
    Fetch currently live tennis events from SofaScore.
    """
    session = create_session()

    url = f"{BASE_URL}/sport/tennis/events/live"

    response = session.get(
        url,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("events", [])

def fetch_tennis_event(
    event_id: int,
) -> dict[str, Any]:
    """
    Fetch one specific tennis event from SofaScore.

    This endpoint can return both live and finished
    matches, unlike the live-events endpoint.
    """

    session = create_session()

    url = f"{BASE_URL}/event/{event_id}"

    response = session.get(
        url,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    event = data.get("event")

    if not event:
        raise RuntimeError(
            f"SofaScore event {event_id} was not found."
        )

    return event


def is_professional_singles_event(
    event: dict[str, Any],
) -> bool:
    """
    Determine whether a SofaScore event is professional
    singles tennis.

    Includes professional competitions such as:
        ATP
        WTA
        ATP Challenger
        ITF
        Grand Slams
        Davis Cup
        Billie Jean King Cup
        United Cup

    Excludes:
        UTR
        Junior events
        Amateur events
        Doubles
    """

    event_filters = event.get("eventFilters") or {}

    categories = event_filters.get("category") or []
    levels = event_filters.get("level") or []
    genders = event_filters.get("gender") or []

    # ---------------------------------------------------------
    # 1. Must be singles.
    # ---------------------------------------------------------

    if "singles" not in categories:
        return False

    # ---------------------------------------------------------
    # 2. Must be professional.
    # ---------------------------------------------------------

    if "pro" not in levels:
        return False

    # ---------------------------------------------------------
    # 3. Must have a recognized tennis gender.
    # ---------------------------------------------------------

    if not any(
        gender in {"M", "W"}
        for gender in genders
    ):
        return False

    # ---------------------------------------------------------
    # 4. Get tournament information.
    # ---------------------------------------------------------

    tournament = event.get("tournament") or {}

    tournament_name = (
        tournament.get("name")
        or ""
    ).lower()

    tournament_slug = (
        tournament.get("slug")
        or ""
    ).lower()

    unique_tournament = (
        tournament.get("uniqueTournament")
        or {}
    )

    unique_name = (
        unique_tournament.get("name")
        or ""
    ).lower()

    unique_slug = (
        unique_tournament.get("slug")
        or ""
    ).lower()

    season = event.get("season") or {}

    season_name = (
        season.get("name")
        or ""
    ).lower()

    # Combine tournament-related names so we can
    # reliably detect unwanted competitions.

    combined_text = " ".join(
        [
            tournament_name,
            tournament_slug,
            unique_name,
            unique_slug,
            season_name,
        ]
    )

    # ---------------------------------------------------------
    # 5. Exclude UTR.
    # ---------------------------------------------------------

    excluded_keywords = [
        "utr",
        "junior",
        "juniors",
        "u18",
        "u16",
        "u14",
        "u12",
        "amateur",
    ]

    if any(
        keyword in combined_text
        for keyword in excluded_keywords
    ):
        return False

    # ---------------------------------------------------------
    # 6. Additional doubles safeguard.
    # ---------------------------------------------------------

    doubles_keywords = [
        "doubles",
        "double",
        "men's doubles",
        "women's doubles",
        "mixed doubles",
    ]

    if any(
        keyword in combined_text
        for keyword in doubles_keywords
    ):
        return False

    # ---------------------------------------------------------
    # 7. Keep recognized professional competitions.
    # ---------------------------------------------------------

    allowed_keywords = [
        "atp",
        "wta",
        "challenger",
        "itf",
        "grand slam",
        "australian open",
        "french open",
        "roland garros",
        "wimbledon",
        "us open",
        "davis cup",
        "billie jean king cup",
        "united cup",
        "hopman cup",
    ]

    return any(
        keyword in combined_text
        for keyword in allowed_keywords
    )


def get_player_data(
    player: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Extract useful player information.
    """

    if not player:
        return {
            "id": None,
            "name": None,
            "short_name": None,
            "gender": None,
            "ranking": None,
            "country": None,
            "country_code": None,
        }

    country = player.get("country") or {}

    return {
        "id": player.get("id"),
        "name": player.get("name"),
        "short_name": player.get("shortName"),
        "gender": player.get("gender"),
        "ranking": player.get("ranking"),
        "country": country.get("name"),
        "country_code": country.get("alpha2"),
    }


def get_score_value(
    score: dict[str, Any] | None,
    key: str,
) -> int | None:
    """
    Safely extract an integer score.
    """

    if not score:
        return None

    value = score.get(key)

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_set_scores(
    home_score: dict[str, Any] | None,
    away_score: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """
    Extract all tennis set scores.

    SofaScore exposes tennis sets as:
        period1
        period2
        period3
        period4
        period5

    An active set can also appear here with its current game score.
    """

    home_score = home_score or {}
    away_score = away_score or {}

    sets = []

    for set_number in range(1, 6):
        period_key = f"period{set_number}"

        home_value = get_score_value(
            home_score,
            period_key,
        )

        away_value = get_score_value(
            away_score,
            period_key,
        )

        if home_value is None and away_value is None:
            continue

        sets.append(
            {
                "set_number": set_number,
                "home": home_value,
                "away": away_value,
            }
        )

    return sets


def get_current_game_points(
    home_score: dict[str, Any],
    away_score: dict[str, Any],
) -> dict[str, Any]:
    """
    Get the current tennis game points.

    Examples:
        0
        15
        30
        40
        A

    SofaScore may provide these as strings.
    """

    return {
        "home": home_score.get("point"),
        "away": away_score.get("point"),
    }


def get_current_set_number(
    event: dict[str, Any],
) -> int | None:
    """
    Determine which set is currently being played.

    SofaScore provides lastPeriod such as:
        period1
        period2
        period3
        period4
        period5
    """

    last_period = event.get("lastPeriod")

    if not last_period:
        return None

    if not last_period.startswith("period"):
        return None

    try:
        return int(
            last_period.replace("period", "")
        )
    except ValueError:
        return None


def get_start_time(
    timestamp: Any,
) -> str | None:
    """
    Convert SofaScore Unix timestamp into UTC ISO format.
    """

    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc,
        ).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def normalize_event(
    event: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a raw SofaScore tennis event into
    Atletiks' normalized structure.
    """

    tournament = event.get("tournament") or {}

    unique_tournament = (
        tournament.get("uniqueTournament") or {}
    )

    category = tournament.get("category") or {}

    season = event.get("season") or {}

    round_info = event.get("roundInfo") or {}

    status = event.get("status") or {}

    home_player = get_player_data(
        event.get("homeTeam")
    )

    away_player = get_player_data(
        event.get("awayTeam")
    )

    home_score = event.get("homeScore") or {}

    away_score = event.get("awayScore") or {}

    current_set_number = get_current_set_number(
        event
    )

    set_scores = extract_set_scores(
        home_score,
        away_score,
    )

    current_game_points = get_current_game_points(
        home_score,
        away_score,
    )

    return {
        "sofascore_event_id": event.get("id"),

        "custom_id": event.get("customId"),

        "slug": event.get("slug"),

        "sport": "tennis",

        "gender": (
            home_player["gender"]
            or away_player["gender"]
        ),

        "home_player": home_player,

        "away_player": away_player,

        "tournament": {
            "id": unique_tournament.get(
                "id"
            ),
            "name": unique_tournament.get(
                "name"
            )
            or tournament.get("name"),
            "slug": unique_tournament.get(
                "slug"
            )
            or tournament.get("slug"),
            "category": category.get("name"),
            "ground_type": (
                unique_tournament.get(
                    "groundType"
                )
            ),
            "tennis_points": (
                unique_tournament.get(
                    "tennisPoints"
                )
            ),
        },

        "season": {
            "id": season.get("id"),
            "name": season.get("name"),
            "year": season.get("year"),
        },

        "round": {
            "number": round_info.get("round"),
            "name": round_info.get("name"),
            "slug": round_info.get("slug"),
        },

        "status": {
            "type": status.get("type"),
            "description": status.get(
                "description"
            ),
            "code": status.get("code"),
        },

        "start_time": get_start_time(
            event.get("startTimestamp")
        ),

        "current_set": {
            "number": current_set_number,

            "home_games": (
                get_score_value(
                    home_score,
                    f"period{current_set_number}",
                )
                if current_set_number
                else None
            ),

            "away_games": (
                get_score_value(
                    away_score,
                    f"period{current_set_number}",
                )
                if current_set_number
                else None
            ),
        },

        "score": {
            "home_sets": get_score_value(
                home_score,
                "current",
            ),

            "away_sets": get_score_value(
                away_score,
                "current",
            ),

            "sets": set_scores,

            "current_game_points": (
                current_game_points
            ),
        },

        "first_to_serve": event.get(
            "firstToServe"
        ),

        "ground_type": event.get(
            "groundType"
        ),

        "event_filters": (
            event.get("eventFilters") or {}
        ),
    }


def get_live_professional_singles() -> list[dict[str, Any]]:
    """
    Fetch and normalize all currently live
    professional singles tennis matches.
    """

    events = fetch_live_tennis_events()

    matches = []

    for event in events:

        if not is_professional_singles_event(
            event
        ):
            continue

        matches.append(
            normalize_event(event)
        )

    return matches


def print_matches(
    matches: list[dict[str, Any]],
) -> None:
    """
    Print normalized tennis matches.
    """

    print()
    print("=" * 80)
    print("ATLETIKS - LIVE PROFESSIONAL TENNIS")
    print("=" * 80)

    if not matches:
        print(
            "No professional singles matches "
            "are currently live."
        )

        print("=" * 80)

        return

    for match in matches:

        home = match["home_player"]

        away = match["away_player"]

        tournament = match["tournament"]

        round_info = match["round"]

        status = match["status"]

        score = match["score"]

        current_set = match["current_set"]

        print()

        print(
            f"{home['name']} "
            f"vs "
            f"{away['name']}"
        )

        print(
            f"Tournament: "
            f"{tournament['name']}"
        )

        print(
            f"Category: "
            f"{tournament['category']}"
        )

        print(
            f"Surface: "
            f"{tournament['ground_type']}"
        )

        print(
            f"Round: "
            f"{round_info['name']}"
        )

        print(
            f"Status: "
            f"{status['type']} "
            f"({status['description']})"
        )

        print(
            f"Completed sets: "
            f"{score['home_sets']} - "
            f"{score['away_sets']}"
        )

        if current_set["number"]:

            print(
                f"Current set: "
                f"Set {current_set['number']}"
            )

            print(
                f"Current set score: "
                f"{current_set['home_games']} - "
                f"{current_set['away_games']}"
            )

        print(
            f"Current game points: "
            f"{score['current_game_points']['home']} - "
            f"{score['current_game_points']['away']}"
        )

        if score["sets"]:

            print("Set scores:")

            for tennis_set in score["sets"]:

                print(
                    f"  Set "
                    f"{tennis_set['set_number']}: "
                    f"{tennis_set['home']} - "
                    f"{tennis_set['away']}"
                )

        print(
            f"SofaScore event ID: "
            f"{match['sofascore_event_id']}"
        )

        print("-" * 80)


def main():
    matches = get_live_professional_singles()

    print_matches(matches)


if __name__ == "__main__":
    main()