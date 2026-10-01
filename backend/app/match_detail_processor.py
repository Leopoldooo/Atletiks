from app.database import get_connection


def get_performance_score(player):
    points = player.get("points") or 0
    rebounds = player.get("rebounds") or 0
    assists = player.get("assists") or 0
    steals = player.get("steals") or 0
    blocks = player.get("blocks") or 0
    turnovers = player.get("turnovers") or 0

    return (
        points
        + rebounds * 1.2
        + assists * 1.5
        + steals * 2
        + blocks * 2
        - turnovers * 1.5
    )


def has_played(player):
    minutes = player.get("minutes")

    if minutes is None:
        return False

    minutes = str(minutes).strip()

    if not minutes:
        return False

    if minutes in ("0", "0:00", "00:00"):
        return False

    return True


def calculate_performers(players, team_ids):
    best_performers = []
    lowest_performers = []

    for team_id in team_ids:
        team_players = [
            player
            for player in players
            if player["team_id"] == team_id
            and has_played(player)
        ]

        if not team_players:
            continue

        for player in team_players:
            player["performance_score"] = round(
                get_performance_score(player),
                2
            )

        team_players_sorted = sorted(
            team_players,
            key=lambda player: player["performance_score"],
            reverse=True
        )

        best_player = team_players_sorted[0]
        worst_player = team_players_sorted[-1]

        best_performers.append({
            "player_id": best_player["player_id"],
            "player_name": best_player["player_name"],
            "team_id": best_player["team_id"],
            "team_name": best_player["team_name"],
            "minutes": best_player["minutes"],
            "points": best_player["points"],
            "rebounds": best_player["rebounds"],
            "assists": best_player["assists"],
            "steals": best_player["steals"],
            "blocks": best_player["blocks"],
            "turnovers": best_player["turnovers"],
            "performance_score": best_player["performance_score"]
        })

        lowest_performers.append({
            "player_id": worst_player["player_id"],
            "player_name": worst_player["player_name"],
            "team_id": worst_player["team_id"],
            "team_name": worst_player["team_name"],
            "minutes": worst_player["minutes"],
            "points": worst_player["points"],
            "rebounds": worst_player["rebounds"],
            "assists": worst_player["assists"],
            "steals": worst_player["steals"],
            "blocks": worst_player["blocks"],
            "turnovers": worst_player["turnovers"],
            "performance_score": worst_player["performance_score"]
        })

    return best_performers, lowest_performers


def get_match_details(match_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                m.id,
                m.external_id,
                m.source_name,
                m.league_id,
                l.name AS league_name,
                m.home_team_id,
                ht.name AS home_team_name,
                m.away_team_id,
                at.name AS away_team_name,
                m.scheduled_at,
                m.status,
                m.venue,
                m.current_period,
                m.current_period_type,
                m.game_clock,
                m.home_team_score,
                m.away_team_score
            FROM matches m
            LEFT JOIN leagues l
                ON l.id = m.league_id
            LEFT JOIN teams ht
                ON ht.id = m.home_team_id
            LEFT JOIN teams at
                ON at.id = m.away_team_id
            WHERE m.id = %s
            LIMIT 1;
        """, (match_id,))

        match = cursor.fetchone()

        if not match:
            return None

        match_columns = [
            "id",
            "external_id",
            "source_name",
            "league_id",
            "league_name",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "scheduled_at",
            "status",
            "venue",
            "current_period",
            "current_period_type",
            "game_clock",
            "home_team_score",
            "away_team_score"
        ]

        match_data = dict(zip(match_columns, match))

        cursor.execute("""
            SELECT
                mps.team_id,
                t.name AS team_name,
                mps.period_number,
                mps.period_type,
                mps.score
            FROM match_period_scores mps
            JOIN teams t
                ON t.id = mps.team_id
            WHERE mps.match_id = %s
            ORDER BY
                mps.period_number,
                mps.team_id;
        """, (match_id,))

        period_rows = cursor.fetchall()

        periods = []

        for row in period_rows:
            periods.append({
                "team_id": row[0],
                "team_name": row[1],
                "period_number": row[2],
                "period_type": row[3],
                "score": row[4]
            })

        cursor.execute("""
            SELECT
                pms.player_id,
                p.name AS player_name,
                pms.team_id,
                t.name AS team_name,
                pms.is_starter,
                pms.minutes,
                pms.points,
                pms.field_goals_made,
                pms.field_goals_attempted,
                pms.three_pointers_made,
                pms.three_pointers_attempted,
                pms.free_throws_made,
                pms.free_throws_attempted,
                pms.rebounds,
                pms.assists,
                pms.turnovers,
                pms.steals,
                pms.blocks,
                pms.offensive_rebounds,
                pms.defensive_rebounds,
                pms.personal_fouls,
                pms.plus_minus
            FROM player_match_stats pms
            JOIN players p
                ON p.id = pms.player_id
            LEFT JOIN teams t
                ON t.id = pms.team_id
            WHERE pms.match_id = %s
            ORDER BY
                pms.team_id,
                pms.is_starter DESC,
                pms.points DESC;
        """, (match_id,))

        player_rows = cursor.fetchall()

        players = []

        for row in player_rows:
            players.append({
                "player_id": row[0],
                "player_name": row[1],
                "team_id": row[2],
                "team_name": row[3],
                "is_starter": row[4],
                "minutes": row[5],
                "points": row[6],
                "field_goals_made": row[7],
                "field_goals_attempted": row[8],
                "three_pointers_made": row[9],
                "three_pointers_attempted": row[10],
                "free_throws_made": row[11],
                "free_throws_attempted": row[12],
                "rebounds": row[13],
                "assists": row[14],
                "turnovers": row[15],
                "steals": row[16],
                "blocks": row[17],
                "offensive_rebounds": row[18],
                "defensive_rebounds": row[19],
                "personal_fouls": row[20],
                "plus_minus": row[21]
            })

        # Calculate team totals from player statistics.
        team_totals = {}

        for player in players:
            team_id = player["team_id"]

            if team_id not in team_totals:
                team_totals[team_id] = {
                    "team_id": team_id,
                    "team_name": player["team_name"],
                    "points": 0,
                    "field_goals_made": 0,
                    "field_goals_attempted": 0,
                    "three_pointers_made": 0,
                    "three_pointers_attempted": 0,
                    "free_throws_made": 0,
                    "free_throws_attempted": 0,
                    "rebounds": 0,
                    "assists": 0,
                    "turnovers": 0,
                    "steals": 0,
                    "blocks": 0,
                    "offensive_rebounds": 0,
                    "defensive_rebounds": 0,
                    "personal_fouls": 0
                }

            totals = team_totals[team_id]

            totals["points"] += player["points"] or 0
            totals["field_goals_made"] += (
                player["field_goals_made"] or 0
            )
            totals["field_goals_attempted"] += (
                player["field_goals_attempted"] or 0
            )
            totals["three_pointers_made"] += (
                player["three_pointers_made"] or 0
            )
            totals["three_pointers_attempted"] += (
                player["three_pointers_attempted"] or 0
            )
            totals["free_throws_made"] += (
                player["free_throws_made"] or 0
            )
            totals["free_throws_attempted"] += (
                player["free_throws_attempted"] or 0
            )
            totals["rebounds"] += player["rebounds"] or 0
            totals["assists"] += player["assists"] or 0
            totals["turnovers"] += player["turnovers"] or 0
            totals["steals"] += player["steals"] or 0
            totals["blocks"] += player["blocks"] or 0
            totals["offensive_rebounds"] += (
                player["offensive_rebounds"] or 0
            )
            totals["defensive_rebounds"] += (
                player["defensive_rebounds"] or 0
            )
            totals["personal_fouls"] += (
                player["personal_fouls"] or 0
            )

        team_ids = [
            match_data["home_team_id"],
            match_data["away_team_id"]
        ]

        best_performers, lowest_performers = calculate_performers(
            players,
            team_ids
        )

        return {
            "match": match_data,
            "periods": periods,
            "team_totals": list(team_totals.values()),
            "players": players,
            "best_performers": best_performers,
            "lowest_performers": lowest_performers
        }

    finally:
        cursor.close()
        connection.close()