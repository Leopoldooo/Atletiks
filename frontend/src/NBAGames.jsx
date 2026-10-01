import { useEffect, useRef, useState } from "react";

function formatLivePeriod(match) {
  if (!match.current_period) {
    return "Live";
  }

  if (match.current_period_type === "Overtime") {
    const overtimeNumber = match.current_period - 4;

    return overtimeNumber > 1
      ? `OT${overtimeNumber}`
      : "OT";
  }

  return `Q${match.current_period}`;
}

function formatGameDate(date) {
  if (!date) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Manila",
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(date));
}

function formatPhilippineTime(date) {
  if (!date) {
    return "Time unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Manila",
    hour: "numeric",
    minute: "2-digit",
    hour12: true
  }).format(new Date(date));
}

function formatUSEasternTime(date) {
  if (!date) {
    return "Time unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZoneName: "short"
  }).format(new Date(date));
}

function getPhilippineDateKey(date) {
  if (!date) {
    return "";
  }

  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(date));
}

function getTodayPhilippineDateKey() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date());
}

function NBAGames({ onSelectGame }) {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetchMatches() {
    try {
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/matches"
      );

      if (!response.ok) {
        throw new Error("Failed to load NBA games");
      }

      const data = await response.json();

      const nbaMatches = data.filter(
        (match) => match.league === "NBA"
      );

      setMatches(nbaMatches);
    } catch (err) {
      console.error("NBA Games Error:", err);
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchMatches();

    const interval = setInterval(() => {
      fetchMatches();
    }, 15000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const getGameCategory = (match) => {
    const status = (match.status || "").toLowerCase();

    if (
      status === "final" ||
      status.includes("final") ||
      status === "completed"
    ) {
      return "completed";
    }

    if (
      status.includes("live") ||
      status.includes("progress") ||
      status.includes("halftime") ||
      status.includes("in progress")
    ) {
      return "live";
    }

    return "upcoming";
  };

  if (loading) {
    return (
      <section className="section nba-page">
        <div className="nba-loading">
          <div className="nba-loading-line"></div>
          <div className="nba-loading-line short"></div>
          <p>Loading NBA games...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="section nba-page">
        <div className="nba-error">
          <p className="section-label">NBA</p>
          <h3>Unable to load games</h3>
          <p>{error}</p>
        </div>
      </section>
    );
  }

  const todayKey = getTodayPhilippineDateKey();

  /*
   * LIVE GAMES
   * These always go into the first section.
   */
  const liveGames = matches
    .filter((match) => getGameCategory(match) === "live")
    .sort(
      (a, b) =>
        new Date(a.scheduled_at) -
        new Date(b.scheduled_at)
    );

  /*
   * ALL SCHEDULED / UPCOMING GAMES
   */
  const scheduledGames = matches
    .filter((match) => getGameCategory(match) === "upcoming");

  /*
   * TODAY'S SCHEDULED GAMES
   * Uses Philippine calendar date.
   */
  const todayGames = scheduledGames
    .filter(
      (match) =>
        getPhilippineDateKey(match.scheduled_at) === todayKey
    )
    .sort(
      (a, b) =>
        new Date(a.scheduled_at) -
        new Date(b.scheduled_at)
    );

  /*
   * FUTURE GAMES
   * Anything scheduled after today.
   */
  const futureGames = scheduledGames
    .filter(
      (match) =>
        getPhilippineDateKey(match.scheduled_at) > todayKey
    )
    .sort(
      (a, b) =>
        new Date(a.scheduled_at) -
        new Date(b.scheduled_at)
    );

  /*
   * COMPLETED GAMES
   */
  const completedGames = matches
    .filter((match) => getGameCategory(match) === "completed")
    .sort(
      (a, b) =>
        new Date(b.scheduled_at) -
        new Date(a.scheduled_at)
    );

  /*
   * FIRST SECTION
   *
   * Live games appear first.
   * Today's scheduled games appear after them.
   */
  const liveTodayGames = [
    ...liveGames,
    ...todayGames
  ];

  const GameCard = ({ match }) => {
    const category = getGameCategory(match);

    const isLive = category === "live";
    const isCompleted = category === "completed";

    return (
      <button
        className={`nba-game-card ${
          isLive ? "live" : ""
        } ${isCompleted ? "completed" : ""}`}
        onClick={() => onSelectGame(match.id)}
      >
        <div className="nba-game-card-top">
          <span
            className={`nba-game-status ${
              isLive ? "live" : ""
            }`}
          >
            {isLive
              ? "LIVE"
              : isCompleted
                ? "FINAL"
                : "UPCOMING"}
          </span>

          <span className="nba-game-league">
            NBA
          </span>
        </div>

        <div className="nba-matchup">
          <div className="nba-team">
            <div className="nba-team-placeholder">
              {match.away_team
                ? match.away_team.charAt(0)
                : "A"}
            </div>

            <span>{match.away_team}</span>
          </div>

          <div className="nba-game-center">
            {isLive || isCompleted ? (
              <>
                <strong>
                  {match.away_team_score ?? 0}
                </strong>

                <span className="nba-score-divider">
                  -
                </span>

                <strong>
                  {match.home_team_score ?? 0}
                </strong>
              </>
            ) : (
              <span className="nba-at">@</span>
            )}
          </div>

          <div className="nba-team home">
            <div className="nba-team-placeholder">
              {match.home_team
                ? match.home_team.charAt(0)
                : "H"}
            </div>

            <span>{match.home_team}</span>
          </div>
        </div>

        {isLive && (
          <div className="game-live-info">
            <span>
              {formatLivePeriod(match)}
            </span>

            {match.game_clock && (
              <span>
                {" · "}
                {match.game_clock}
              </span>
            )}
          </div>
        )}

        <div className="nba-game-card-bottom">
          {isLive ? (
            <div className="nba-game-time">
              <span className="nba-game-date">
                {formatGameDate(match.scheduled_at)}
              </span>

              <span>
                Live now
              </span>
            </div>
          ) : (
            <div className="nba-game-time">
              <span className="nba-game-date">
                {formatGameDate(match.scheduled_at)}
              </span>

              <span className="nba-time-line">
                PH {formatPhilippineTime(match.scheduled_at)}
              </span>

              <span className="nba-time-line">
                US {formatUSEasternTime(match.scheduled_at)}
              </span>
            </div>
          )}

          <span className="nba-card-arrow">
            →
          </span>
        </div>
      </button>
    );
  };

  const GameCarousel = ({
    title,
    label,
    games,
    type
  }) => {
    const carouselRef = useRef(null);

    const scrollCarousel = (direction) => {
      if (!carouselRef.current) {
        return;
      }

      const card = carouselRef.current.querySelector(
        ".nba-game-card"
      );

      if (!card) {
        return;
      }

      const cardWidth =
        card.getBoundingClientRect().width;

      const gap = 14;

      carouselRef.current.scrollBy({
        left:
          direction === "next"
            ? cardWidth + gap
            : -(cardWidth + gap),
        behavior: "smooth"
      });
    };

    return (
      <div className={`nba-game-group ${type}`}>
        <div className="nba-carousel-header">
          <div>
            <p className="section-label">
              {label}
            </p>

            <h3>{title}</h3>
          </div>

          <div className="nba-carousel-controls">
            <button
              type="button"
              className="nba-carousel-button"
              onClick={() =>
                scrollCarousel("previous")
              }
              aria-label={`Previous ${title}`}
            >
              ←
            </button>

            <button
              type="button"
              className="nba-carousel-button"
              onClick={() =>
                scrollCarousel("next")
              }
              aria-label={`Next ${title}`}
            >
              →
            </button>
          </div>
        </div>

        <div
          className="nba-games-carousel"
          ref={carouselRef}
        >
          {games.map((match) => (
            <GameCard
              key={match.id}
              match={match}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <section className="section nba-page">
      <div className="section-header nba-page-header">
        <div>
          <p className="section-label">
            NBA
          </p>

          <h3>Games</h3>
        </div>
      </div>

      {/* 1. LIVE / TODAY */}
      {liveTodayGames.length > 0 && (
        <GameCarousel
          label="Live / Today"
          title="Live / Today Games"
          games={liveTodayGames}
          type="live-today"
        />
      )}

      {/* 2. COMPLETED */}
      {completedGames.length > 0 && (
        <GameCarousel
          label="Completed"
          title="Completed Games"
          games={completedGames}
          type="completed"
        />
      )}

      {/* 3. UPCOMING */}
      {futureGames.length > 0 && (
        <GameCarousel
          label="Upcoming"
          title="Upcoming Games"
          games={futureGames}
          type="upcoming"
        />
      )}

      {matches.length === 0 && (
        <div className="empty-state">
          <p>No NBA games available.</p>
        </div>
      )}
    </section>
  );
}

export default NBAGames;