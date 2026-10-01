from curl_cffi import requests


URL = "https://www.sofascore.com/api/v1/sport/tennis/events/live"


def main():
    print("Testing Sofascore live tennis API...")
    print(f"URL: {URL}")
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
            print("Response:")
            print(response.text[:1000])
            return

        data = response.json()

        events = data.get("events", [])

        print(f"Live tennis events found: {len(events)}")
        print()

        if not events:
            print("No live tennis matches were returned right now.")
            return

        for event in events:
            event_id = event.get("id")
            status = event.get("status", {})

            home = event.get("homeTeam", {}).get("name", "Unknown")
            away = event.get("awayTeam", {}).get("name", "Unknown")

            home_score = event.get("homeScore", {})
            away_score = event.get("awayScore", {})

            home_current = home_score.get("current", "-")
            away_current = away_score.get("current", "-")

            tournament = event.get("tournament", {}).get("name", "Unknown")

            print("=" * 70)
            print(f"Event ID: {event_id}")
            print(f"Match: {home} vs {away}")
            print(f"Score: {home_current} - {away_current}")
            print(f"Tournament: {tournament}")
            print(f"Status: {status.get('type', 'Unknown')}")
            print(f"Description: {status.get('description', 'Unknown')}")
            print()

    except Exception as e:
        print("ERROR:")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    main()