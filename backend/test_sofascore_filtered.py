from curl_cffi import requests


URL = "https://www.sofascore.com/api/v1/sport/tennis/events/live"


def main():
    print("Testing filtered Sofascore tennis events...")
    print()

    try:
        response = requests.get(
            URL,
            impersonate="chrome",
            timeout=20,
        )

        print(f"HTTP Status: {response.status_code}")
        print()

        if response.status_code != 200:
            print("Request failed.")
            print(response.text[:2000])
            return

        data = response.json()
        events = data.get("events", [])

        filtered_events = []

        for event in events:
            tournament = event.get("tournament", {})
            category = tournament.get("category", {})

            category_name = str(category.get("name", "")).upper()

            event_filters = event.get("eventFilters", {})

            event_category = event_filters.get("category", [])
            event_level = event_filters.get("level", [])
            event_gender = event_filters.get("gender", [])

            is_atp_or_wta = category_name in ["ATP", "WTA"]

            home_name = event.get("homeTeam", {}).get("name", "")
            away_name = event.get("awayTeam", {}).get("name", "")

            has_doubles_names = (
                "/" in home_name
                or "/" in away_name
            )

            is_singles = (
                "singles" in event_category
                and not has_doubles_names
            )

            is_pro = "pro" in event_level

            if is_atp_or_wta and is_singles and is_pro:
                filtered_events.append(event)

        print(f"Total live tennis events: {len(events)}")
        print(f"ATP/WTA singles events: {len(filtered_events)}")
        print()

        if not filtered_events:
            print("No ATP/WTA singles matches are currently live.")
            return

        for event in filtered_events:
            tournament = event.get("tournament", {})
            category = tournament.get("category", {})

            home = event.get("homeTeam", {})
            away = event.get("awayTeam", {})

            home_score = event.get("homeScore", {})
            away_score = event.get("awayScore", {})

            status = event.get("status", {})

            print("=" * 75)

            print(f"Sofascore ID: {event.get('id')}")
            print(
                f"Tour: {category.get('name', 'Unknown')}"
            )
            print(
                f"Match: {home.get('name', 'Unknown')} "
                f"vs "
                f"{away.get('name', 'Unknown')}"
            )

            print(
                f"Score: "
                f"{home_score.get('current', '-')} - "
                f"{away_score.get('current', '-')}"
            )

            print(
                f"Set 1: "
                f"{home_score.get('period1', '-')} - "
                f"{away_score.get('period1', '-')}"
            )

            print(
                f"Set 2: "
                f"{home_score.get('period2', '-')} - "
                f"{away_score.get('period2', '-')}"
            )

            print(
                f"Set 3: "
                f"{home_score.get('period3', '-')} - "
                f"{away_score.get('period3', '-')}"
            )

            print(
                f"Current set: "
                f"{status.get('description', 'Unknown')}"
            )

            print(
                f"Status: "
                f"{status.get('type', 'Unknown')}"
            )

            print(
                f"Tournament: "
                f"{tournament.get('name', 'Unknown')}"
            )

            print()

    except Exception as e:
        print("ERROR:")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    main()