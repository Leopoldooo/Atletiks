from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_connection
from app.nba_processor import filter_nba_teams
from app.nba_games_processor import process_nba_games
from app.nba_period_processor import process_nba_period_score_row
from app.nba_player_stats_processor import process_nba_player_stats
from app.espn_games_processor import process_espn_game
from app.nba_player_processor import process_nba_players
from app.espn_period_processor import process_espn_periods
from app.match_detail_processor import get_match_details


app = FastAPI(
    title="Atletiks API",
    description="Sports data API for Atletiks",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Atletiks API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/sports")
def get_sports():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name
            FROM sports
            ORDER BY id;
        """)

        sports = cursor.fetchall()

        return [
            {
                "id": sport[0],
                "name": sport[1]
            }
            for sport in sports
        ]

    finally:
        cursor.close()
        connection.close()


@app.get("/leagues")
def get_leagues():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                leagues.id,
                leagues.name,
                leagues.country,
                sports.name AS sport
            FROM leagues
            JOIN sports
                ON leagues.sport_id = sports.id
            ORDER BY leagues.id;
        """)

        leagues = cursor.fetchall()

        return [
            {
                "id": league[0],
                "name": league[1],
                "country": league[2],
                "sport": league[3]
            }
            for league in leagues
        ]

    finally:
        cursor.close()
        connection.close()

@app.get("/teams")
def get_teams():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                teams.id,
                teams.name,
                teams.short_name,
                teams.country,
                teams.logo_url,
                leagues.name AS league
            FROM teams
            LEFT JOIN leagues
                ON teams.league_id = leagues.id
            ORDER BY teams.id;
        """)

        teams = cursor.fetchall()

        return [
            {
                "id": team[0],
                "name": team[1],
                "short_name": team[2],
                "country": team[3],
                "logo_url": team[4],
                "league": team[5]
            }
            for team in teams
        ]

    finally:
        cursor.close()
        connection.close()


@app.get("/players")
def get_players():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                players.id,
                players.name,
                players.first_name,
                players.last_name,
                players.country,
                players.birth_date,
                players.photo_url,
                sports.name AS sport
            FROM players
            LEFT JOIN sports
                ON players.sport_id = sports.id
            ORDER BY players.id;
        """)

        players = cursor.fetchall()

        return [
            {
                "id": player[0],
                "name": player[1],
                "first_name": player[2],
                "last_name": player[3],
                "country": player[4],
                "birth_date": player[5],
                "photo_url": player[6],
                "sport": player[7]
            }
            for player in players
        ]

    finally:
        cursor.close()
        connection.close()


@app.get("/matches")
def get_matches():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
    SELECT DISTINCT ON (
        matches.scheduled_at,
        matches.home_team_id,
        matches.away_team_id
    )
        matches.id,
        matches.scheduled_at,
        matches.status,
        matches.venue,
        leagues.name AS league,
        home_team.name AS home_team,
        away_team.name AS away_team,
        matches.home_team_score,
matches.away_team_score,
matches.current_period,
matches.current_period_type,
matches.game_clock
    FROM matches
    LEFT JOIN leagues
        ON matches.league_id = leagues.id
    LEFT JOIN teams AS home_team
        ON matches.home_team_id = home_team.id
    LEFT JOIN teams AS away_team
        ON matches.away_team_id = away_team.id
    ORDER BY
        matches.scheduled_at DESC NULLS LAST,
        matches.home_team_id,
        matches.away_team_id,
        CASE
            WHEN matches.source_name = 'espn' THEN 1
            ELSE 2
        END,
        matches.id DESC;
""")

        matches = cursor.fetchall()

        return [
    {
        "id": match[0],
        "scheduled_at": match[1],
        "status": match[2],
        "venue": match[3],
        "league": match[4],
        "home_team": match[5],
        "away_team": match[6],
        "home_team_score": match[7],
"away_team_score": match[8],
"current_period": match[9],
"current_period_type": match[10],
"game_clock": match[11]
    }
    for match in matches
]

    finally:
        cursor.close()
        connection.close()


@app.get("/news")
def get_news():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                news.id,
                news.title,
                news.description,
                news.url,
                news.image_url,
                news.source_name,
                news.published_at,
                sports.name AS sport,
                leagues.name AS league
            FROM news
            LEFT JOIN sports
                ON news.sport_id = sports.id
            LEFT JOIN leagues
                ON news.league_id = leagues.id
            ORDER BY news.published_at DESC NULLS LAST;
        """)

        news = cursor.fetchall()

        return [
            {
                "id": article[0],
                "title": article[1],
                "description": article[2],
                "url": article[3],
                "image_url": article[4],
                "source_name": article[5],
                "published_at": article[6],
                "sport": article[7],
                "league": article[8]
            }
            for article in news
        ]

    finally:
        cursor.close()
        connection.close()

@app.post("/process/nba/teams")
def process_nba_teams(data: dict):
    nba_teams = filter_nba_teams(data)

    return {
        "count": len(nba_teams),
        "teams": nba_teams
    }

@app.post("/process/nba/games")
def process_nba_games_endpoint(data: dict):
    nba_games = process_nba_games(data)

    return {
        "count": len(nba_games),
        "games": nba_games
    }

@app.post("/process/nba/period-scores")
def process_nba_period_scores(data: dict):
    periods = data.get("periods", [])

    processed_periods = []

    for period in periods:
        processed_periods.append({
            "external_id": data.get("external_id"),
            "source_name": data.get("source_name"),

            "home_team_id": data.get("home_team_id"),
            "away_team_id": data.get("away_team_id"),

            "period_number": period.get("period_number"),
            "period_type": period.get("period_type"),

            "home_score": period.get("home_score"),
            "away_score": period.get("away_score")
        })

    return {
        "count": len(processed_periods),
        "periods": processed_periods
    }

@app.post("/process/nba/period-score-row")
def process_nba_period_score_row_endpoint(data: dict):
    return process_nba_period_score_row(data)

@app.post("/process/nba/player-stats")
def process_nba_player_stats_endpoint(data: dict):
    return process_nba_player_stats(data)

@app.post("/process/espn/game")
def process_espn_game_endpoint(data: dict):
    return process_espn_game(data)

@app.post("/process/nba/players")
def process_nba_players_endpoint(data: dict):
    return process_nba_players(data)

@app.post("/process/espn/periods")
def process_espn_periods_endpoint(data: dict):
    return process_espn_periods(data)

@app.get("/matches/{match_id}")
def get_match_details_endpoint(match_id: int):
    result = get_match_details(match_id)

    if result is None:
        return {
            "error": "Match not found"
        }

    return result