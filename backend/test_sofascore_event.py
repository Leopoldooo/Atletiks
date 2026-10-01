from curl_cffi import requests
import json


EVENT_ID = 17201614

URL = f"https://www.sofascore.com/api/v1/event/{EVENT_ID}"


def main():
    print("Testing Sofascore event...")
    print(f"Event ID: {EVENT_ID}")
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
            print(response.text[:2000])
            return

        data = response.json()

        print("Sofascore event data:")
        print()

        print(json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ))

    except Exception as e:
        print("ERROR:")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    main()