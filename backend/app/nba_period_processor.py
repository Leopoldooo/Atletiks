from app.database import get_connection


def get_match_id(external_id, source_name):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM matches
            WHERE source_name = %s
              AND external_id = %s
            LIMIT 1;
        """, (source_name, str(external_id)))

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:
        cursor.close()
        connection.close()


def process_nba_period_score_row(data):
    external_id = data.get("external_id")
    source_name = data.get("source_name")

    match_id = get_match_id(external_id, source_name)

    if match_id is None:
        return {
            "count": 0,
            "period_rows": [],
            "error": f"Match not found for external_id {external_id}"
        }

    home_team_id = data.get("home_team_id")
    away_team_id = data.get("away_team_id")

    period_number = data.get("period_number")
    period_type = data.get("period_type")

    home_score = data.get("home_score")
    away_score = data.get("away_score")

    period_rows = [
        {
            "match_id": match_id,
            "team_id": home_team_id,
            "period_number": period_number,
            "period_type": period_type,
            "score": home_score
        },
        {
            "match_id": match_id,
            "team_id": away_team_id,
            "period_number": period_number,
            "period_type": period_type,
            "score": away_score
        }
    ]

    return {
        "count": len(period_rows),
        "period_rows": period_rows
    }
