-- ============================================
-- ATLETIKS DATABASE SCHEMA
-- ============================================

-- ============================================
-- SPORTS
-- ============================================

CREATE TABLE IF NOT EXISTS sports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- LEAGUES / COMPETITIONS
-- ============================================

CREATE TABLE IF NOT EXISTS leagues (
    id SERIAL PRIMARY KEY,
    sport_id INTEGER NOT NULL REFERENCES sports(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (sport_id, name)
);


-- ============================================
-- TEAMS
-- ============================================

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    short_name VARCHAR(50),
    country VARCHAR(100),
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- PLAYERS
-- ============================================

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    sport_id INTEGER REFERENCES sports(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    country VARCHAR(100),
    birth_date DATE,
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- PLAYER / TEAM MEMBERSHIP
-- ============================================

CREATE TABLE IF NOT EXISTS player_teams (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    start_date DATE,
    end_date DATE,
    jersey_number VARCHAR(20),
    position VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- EVENTS
-- ============================================

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    location VARCHAR(200),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- MATCHES
-- ============================================

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,

    home_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    away_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,

    scheduled_at TIMESTAMP,
    status VARCHAR(50),

    venue VARCHAR(200),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- SCORES
-- ============================================

CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    score INTEGER DEFAULT 0,

    period VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- TRANSACTIONS
-- ============================================

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,

    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,
    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    from_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    to_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,

    transaction_type VARCHAR(100) NOT NULL,

    transaction_date DATE,

    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- NEWS
-- ============================================

CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,

    sport_id INTEGER REFERENCES sports(id) ON DELETE SET NULL,
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,

    title TEXT NOT NULL,
    description TEXT,

    url TEXT NOT NULL,
    image_url TEXT,

    source_name VARCHAR(150),

    published_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (url)
);


-- ============================================
-- TOURNAMENTS
-- ============================================

CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,

    sport_id INTEGER REFERENCES sports(id) ON DELETE SET NULL,
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,

    name VARCHAR(200) NOT NULL,

    location VARCHAR(200),

    start_date DATE,
    end_date DATE,

    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- RANKINGS
-- ============================================

CREATE TABLE IF NOT EXISTS rankings (
    id SERIAL PRIMARY KEY,

    sport_id INTEGER REFERENCES sports(id) ON DELETE SET NULL,
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,

    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,

    ranking_position INTEGER NOT NULL,

    ranking_points NUMERIC,

    ranking_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INITIAL SPORTS
-- ============================================

INSERT INTO sports (name)
VALUES
    ('Basketball'),
    ('Tennis'),
    ('Pickleball'),
    ('MMA'),
    ('Volleyball')
ON CONFLICT (name) DO NOTHING;


-- ============================================
-- INITIAL LEAGUES / COMPETITIONS
-- ============================================

INSERT INTO leagues (sport_id, name, country)
SELECT id, 'NBA', 'United States'
FROM sports
WHERE name = 'Basketball'
ON CONFLICT (sport_id, name) DO NOTHING;


INSERT INTO leagues (sport_id, name, country)
SELECT id, 'PBA', 'Philippines'
FROM sports
WHERE name = 'Basketball'
ON CONFLICT (sport_id, name) DO NOTHING;


INSERT INTO leagues (sport_id, name, country)
SELECT id, 'UAAP Basketball', 'Philippines'
FROM sports
WHERE name = 'Basketball'
ON CONFLICT (sport_id, name) DO NOTHING;


INSERT INTO leagues (sport_id, name, country)
SELECT id, 'Tennis', NULL
FROM sports
WHERE name = 'Tennis'
ON CONFLICT (sport_id, name) DO NOTHING;


INSERT INTO leagues (sport_id, name, country)
SELECT id, 'Pickleball', NULL
FROM sports
WHERE name = 'Pickleball'
ON CONFLICT (sport_id, name) DO NOTHING;


INSERT INTO leagues (sport_id, name, country)
SELECT id, 'UFC', 'United States'
FROM sports
WHERE name = 'MMA'
ON CONFLICT (sport_id, name) DO NOTHING;


INSERT INTO leagues (sport_id, name, country)
SELECT id, 'UAAP Women''s Volleyball', 'Philippines'
FROM sports
WHERE name = 'Volleyball'
ON CONFLICT (sport_id, name) DO NOTHING;