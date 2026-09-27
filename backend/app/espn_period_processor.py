from app.database import get_connection


def get_match_id(external_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM matches
            WHERE source_name = 'espn'
              AND external_id = %s
            LIMIT 1;
        """, (str(external_id),))

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def process_espn_periods(data):
    external_id = data.get("external_id")

    match_id = get_match_id(external_id)

    if match_id is None:
        return {
            "count": 0,
            "period_rows": [],
            "error": (
                "ESPN match not found for external_id "
                f"{external_id}"
            )
        }

    home_team_id = data.get("home_team_id")
    away_team_id = data.get("away_team_id")

    periods = data.get("periods", [])

    period_rows = []

    for period in periods:

        period_number = period.get("period_number")
        period_type = period.get("period_type")

        period_rows.append({
            "match_id": match_id,
            "team_id": home_team_id,
            "period_number": period_number,
            "period_type": period_type,
            "score": period.get("home_score", 0)
        })

        period_rows.append({
            "match_id": match_id,
            "team_id": away_team_id,
            "period_number": period_number,
            "period_type": period_type,
            "score": period.get("away_score", 0)
        })

    return {
        "match_id": match_id,
        "count": len(period_rows),
        "period_rows": period_rows
    }