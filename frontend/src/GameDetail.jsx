import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

function GameDetail({ matchId, onBack }) {
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchGame() {
      try {
        setError("");

        const response = await fetch(
          `http://127.0.0.1:8000/matches/${matchId}`
        );

        if (!response.ok) {
          throw new Error("Failed to load game");
        }

        const data = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        setGame(data);
      } catch (err) {
        console.error("Game Detail Error:", err);
        setError(err.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchGame();

    const interval = setInterval(() => {
      fetchGame();
    }, 15000);

    return () => {
      clearInterval(interval);
    };
  }, [matchId]);

  if (loading) {
    return (
      <section className="game-detail">
        <button className="game-back-button" onClick={onBack}>
          <ArrowLeft size={17} />
          <span>Back to NBA</span>
        </button>

        <div className="game-detail-loading">
          <div className="game-loading-block large"></div>
          <div className="game-loading-block"></div>
          <div className="game-loading-block small"></div>
          <p>Loading game...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="game-detail">
        <button className="game-back-button" onClick={onBack}>
          <ArrowLeft size={17} />
          <span>Back to NBA</span>
        </button>

        <div className="game-detail-error">
          <p className="section-label">NBA</p>
          <h3>Unable to load game</h3>
          <p>{error}</p>
        </div>
      </section>
    );
  }

  if (!game || !game.match) {
    return (
      <section className="game-detail">
        <button className="game-back-button" onClick={onBack}>
          <ArrowLeft size={17} />
          <span>Back to NBA</span>
        </button>

        <div className="game-detail-error">
          <p>Game not found.</p>
        </div>
      </section>
    );
  }

  const {
    match,
    periods = [],
    team_totals = [],
    players = []
  } = game;

  const homePeriods = periods.filter(
    (period) => period.team_id === match.home_team_id
  );

  const awayPeriods = periods.filter(
    (period) => period.team_id === match.away_team_id
  );

  const homePlayers = players.filter(
    (player) => player.team_id === match.home_team_id
  );

  const awayPlayers = players.filter(
    (player) => player.team_id === match.away_team_id
  );

  const homeTotals = team_totals.find(
    (team) => team.team_id === match.home_team_id
  );

  const awayTotals = team_totals.find(
    (team) => team.team_id === match.away_team_id
  );

  const getGameCategory = () => {
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

  const category = getGameCategory();

  const formatDate = (date) => {
    if (!date) {
      return "Date unavailable";
    }

    return new Date(date).toLocaleString();
  };

  const formatPeriodLabel = (period) => {
    if (period.period_type === "Overtime") {
      const overtimeNumber = period.period_number - 4;

      return overtimeNumber > 1
        ? `OT${overtimeNumber}`
        : "OT";
    }

    return `Q${period.period_number}`;
  };

  const formatLivePeriod = () => {
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
  };

  const uniquePeriods = periods.filter(
    (period, index, array) =>
      array.findIndex(
        (item) =>
          item.period_number === period.period_number &&
          item.period_type === period.period_type
      ) === index
  );

  const getStatusLabel = () => {
    if (category === "live") {
      return "LIVE";
    }

    if (category === "completed") {
      return "FINAL";
    }

    return "UPCOMING";
  };

  return (
    <div className="game-detail">
      <button className="game-back-button" onClick={onBack}>
        <ArrowLeft size={17} />
        <span>Back to NBA</span>
      </button>

      {/* =========================
          GAME HERO
          ========================= */}

      <section className={`game-hero ${category}`}>
        <div className="game-hero-top">
          <div>
            <p className="section-label">
              {match.league_name || "NBA"}
            </p>

            <p className="game-hero-date">
              {formatDate(match.scheduled_at)}
            </p>
          </div>

          <div
            className={`game-status-badge ${category}`}
          >
            {getStatusLabel()}
          </div>
        </div>

        <div className="game-main-score">
          <div className="detail-team away">
            <div className="detail-team-logo">
              {match.away_team_name
                ? match.away_team_name.charAt(0)
                : "A"}
            </div>

            <h1>{match.away_team_name}</h1>

            <span className="detail-team-location">
              Away
            </span>
          </div>

          <div className="detail-score-area">
            <div className="detail-score">
              <strong>
                {match.away_team_score ?? 0}
              </strong>

              <span>-</span>

              <strong>
                {match.home_team_score ?? 0}
              </strong>
            </div>

            {category === "live" && (
              <div className="detail-live-indicator">
                <span>{formatLivePeriod()}</span>

                {match.game_clock && (
                  <>
                    <span> · </span>
                    <span>{match.game_clock}</span>
                  </>
                )}
              </div>
            )}

            {category === "upcoming" && (
              <span className="detail-live-indicator">
                Scheduled
              </span>
            )}
          </div>

          <div className="detail-team home">
            <div className="detail-team-logo">
              {match.home_team_name
                ? match.home_team_name.charAt(0)
                : "H"}
            </div>

            <h1>{match.home_team_name}</h1>

            <span className="detail-team-location">
              Home
            </span>
          </div>
        </div>
      </section>

      {/* =========================
          PERIOD SCORES
          ========================= */}

      <section className="game-detail-section">
        <div className="game-detail-section-header">
          <div>
            <p className="section-label">
              GAME
            </p>

            <h3>Score by Period</h3>
          </div>
        </div>

        {periods.length === 0 ? (
          <div className="detail-empty">
            <p>
              No period scores available for this game.
            </p>
          </div>
        ) : (
          <div className="period-score-card">
            <div className="period-score-table">
              <div className="period-score-row period-score-header">
                <div>Team</div>

                {uniquePeriods.map((period) => (
                  <div
                    key={`${period.period_type}-${period.period_number}`}
                  >
                    {formatPeriodLabel(period)}
                  </div>
                ))}

                <div>Total</div>
              </div>

              <PeriodScoreRow
                teamName={match.away_team_name}
                periods={awayPeriods}
                total={match.away_team_score}
                uniquePeriods={uniquePeriods}
              />

              <PeriodScoreRow
                teamName={match.home_team_name}
                periods={homePeriods}
                total={match.home_team_score}
                uniquePeriods={uniquePeriods}
              />
            </div>
          </div>
        )}
      </section>

      {/* =========================
          TEAM TOTALS
          ========================= */}

      <section className="game-detail-section">
        <div className="game-detail-section-header">
          <div>
            <p className="section-label">
              TEAM
            </p>

            <h3>Team Totals</h3>
          </div>
        </div>

        {team_totals.length === 0 ? (
          <div className="detail-empty">
            <p>
              No team statistics available for this game.
            </p>
          </div>
        ) : (
          <div className="team-total-cards">
            <TeamTotalCard
              team={awayTotals}
              fallbackName={match.away_team_name}
            />

            <TeamTotalCard
              team={homeTotals}
              fallbackName={match.home_team_name}
            />
          </div>
        )}
      </section>

      {/* =========================
          AWAY PLAYER STATS
          ========================= */}

      <section className="game-detail-section">
        <div className="game-detail-section-header">
          <div>
            <p className="section-label">
              {match.away_team_name}
            </p>

            <h3>Player Statistics</h3>
          </div>

          <span className="player-count">
            {awayPlayers.length} Players
          </span>
        </div>

        {awayPlayers.length === 0 ? (
          <div className="detail-empty">
            <p>
              No player statistics available for{" "}
              {match.away_team_name}.
            </p>
          </div>
        ) : (
          <PlayerTable players={awayPlayers} />
        )}
      </section>

      {/* =========================
          HOME PLAYER STATS
          ========================= */}

      <section className="game-detail-section">
        <div className="game-detail-section-header">
          <div>
            <p className="section-label">
              {match.home_team_name}
            </p>

            <h3>Player Statistics</h3>
          </div>

          <span className="player-count">
            {homePlayers.length} Players
          </span>
        </div>

        {homePlayers.length === 0 ? (
          <div className="detail-empty">
            <p>
              No player statistics available for{" "}
              {match.home_team_name}.
            </p>
          </div>
        ) : (
          <PlayerTable players={homePlayers} />
        )}
      </section>
    </div>
  );
}

function PeriodScoreRow({
  teamName,
  periods,
  total,
  uniquePeriods
}) {
  return (
    <div className="period-score-row">
      <div className="period-team-name">
        {teamName}
      </div>

      {uniquePeriods.map((period) => {
        const matchingPeriod = periods.find(
          (item) =>
            item.period_number ===
              period.period_number &&
            item.period_type === period.period_type
        );

        return (
          <div
            key={`${period.period_type}-${period.period_number}`}
          >
            {matchingPeriod?.score ?? 0}
          </div>
        );
      })}

      <strong>{total ?? 0}</strong>
    </div>
  );
}

function TeamTotalCard({ team, fallbackName }) {
  if (!team) {
    return null;
  }

  return (
    <div className="team-total-card">
      <div className="team-total-header">
        <div>
          <span className="team-total-label">
            TEAM
          </span>

          <h4>
            {team.team_name || fallbackName}
          </h4>
        </div>

        <strong className="team-total-points">
          {team.points ?? 0}
        </strong>
      </div>

      <div className="team-total-grid">
        <StatItem
          label="FG"
          value={`${team.field_goals_made ?? 0}-${team.field_goals_attempted ?? 0}`}
        />

        <StatItem
          label="3PT"
          value={`${team.three_pointers_made ?? 0}-${team.three_pointers_attempted ?? 0}`}
        />

        <StatItem
          label="FT"
          value={`${team.free_throws_made ?? 0}-${team.free_throws_attempted ?? 0}`}
        />

        <StatItem
          label="REB"
          value={team.rebounds ?? 0}
        />

        <StatItem
          label="AST"
          value={team.assists ?? 0}
        />

        <StatItem
          label="TO"
          value={team.turnovers ?? 0}
        />

        <StatItem
          label="STL"
          value={team.steals ?? 0}
        />

        <StatItem
          label="BLK"
          value={team.blocks ?? 0}
        />

        <StatItem
          label="OREB"
          value={team.offensive_rebounds ?? 0}
        />

        <StatItem
          label="DREB"
          value={team.defensive_rebounds ?? 0}
        />

        <StatItem
          label="PF"
          value={team.personal_fouls ?? 0}
        />
      </div>
    </div>
  );
}

function StatItem({ label, value }) {
  return (
    <div className="stat-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PlayerTable({ players }) {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("desc");

  const sortableColumns = [
    { key: "minutes", label: "MIN" },
    { key: "points", label: "PTS" },
    { key: "field_goals_made", label: "FG" },
    { key: "three_pointers_made", label: "3PT" },
    { key: "free_throws_made", label: "FT" },
    { key: "rebounds", label: "REB" },
    { key: "assists", label: "AST" },
    { key: "turnovers", label: "TO" },
    { key: "steals", label: "STL" },
    { key: "blocks", label: "BLK" },
    { key: "offensive_rebounds", label: "OREB" },
    { key: "defensive_rebounds", label: "DREB" },
    { key: "personal_fouls", label: "PF" },
    { key: "plus_minus", label: "+/-" }
  ];

  const getSortableValue = (player, key) => {
    if (key === "minutes") {
      const minutes = player.minutes;

      if (!minutes) {
        return 0;
      }

      const parts = String(minutes).split(":");

      if (parts.length === 2) {
        const minutesPart = Number(parts[0]) || 0;
        const secondsPart = Number(parts[1]) || 0;

        return minutesPart * 60 + secondsPart;
      }

      return Number(minutes) || 0;
    }

    return Number(player[key]) || 0;
  };

  const handleSort = (column) => {
    if (sortColumn !== column) {
      setSortColumn(column);
      setSortDirection("desc");
      return;
    }

    if (sortDirection === "desc") {
      setSortDirection("asc");
      return;
    }

    setSortColumn(null);
    setSortDirection("desc");
  };

  const sortedPlayers = [...players].sort((a, b) => {
    if (!sortColumn) {
      return 0;
    }

    const aValue = getSortableValue(
      a,
      sortColumn
    );

    const bValue = getSortableValue(
      b,
      sortColumn
    );

    if (sortDirection === "desc") {
      return bValue - aValue;
    }

    return aValue - bValue;
  });

  const getSortIndicator = (column) => {
    if (sortColumn !== column) {
      return "";
    }

    return sortDirection === "desc" ? "↓" : "↑";
  };

  return (
    <div className="player-table-container">
      <div className="stats-table-wrapper">
        <table className="stats-table player-stats-table">
          <thead>
            <tr>
              <th>Player</th>

              {sortableColumns.map((column) => (
                <th key={column.key}>
                  <button
                    type="button"
                    className={`player-sort-button ${
                      sortColumn === column.key
                        ? "active"
                        : ""
                    }`}
                    onClick={() =>
                      handleSort(column.key)
                    }
                    aria-label={`Sort by ${column.label}`}
                  >
                    <span>{column.label}</span>

                    <span className="sort-indicator">
                      {getSortIndicator(column.key)}
                    </span>
                  </button>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {sortedPlayers.map((player) => (
              <tr key={player.player_id}>
                <td className="player-name-cell">
                  <div className="player-name">
                    {player.player_name}
                  </div>

                  {player.is_starter && (
                    <span className="starter-label">
                      Starter
                    </span>
                  )}
                </td>

                <td>
                  {player.minutes || "0"}
                </td>

                <td className="points-cell">
                  {player.points ?? 0}
                </td>

                <td>
                  {player.field_goals_made ?? 0}-
                  {player.field_goals_attempted ?? 0}
                </td>

                <td>
                  {player.three_pointers_made ?? 0}-
                  {player.three_pointers_attempted ?? 0}
                </td>

                <td>
                  {player.free_throws_made ?? 0}-
                  {player.free_throws_attempted ?? 0}
                </td>

                <td>
                  {player.rebounds ?? 0}
                </td>

                <td>
                  {player.assists ?? 0}
                </td>

                <td>
                  {player.turnovers ?? 0}
                </td>

                <td>
                  {player.steals ?? 0}
                </td>

                <td>
                  {player.blocks ?? 0}
                </td>

                <td>
                  {player.offensive_rebounds ?? 0}
                </td>

                <td>
                  {player.defensive_rebounds ?? 0}
                </td>

                <td>
                  {player.personal_fouls ?? 0}
                </td>

                <td>
                  {player.plus_minus ?? 0}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mobile-table-hint">
        Swipe horizontally to view more statistics
      </p>
    </div>
  );
}

export default GameDetail;