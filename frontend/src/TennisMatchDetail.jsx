import { useEffect, useMemo, useState } from "react";

function isLiveMatch(status) {
  const value = String(status || "").toLowerCase();

  return (
    value.includes("live") ||
    value.includes("progress") ||
    value.includes("in progress") ||
    value.includes("halftime")
  );
}

function formatPhilippineDate(dateValue) {
  if (!dateValue) {
    return "";
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("en-PH", {
    timeZone: "Asia/Manila",
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function getPlayer(match, order) {
  return (match.players || []).find(
    (player) => player.participant_order === order
  );
}

function getPlayerSetScore(setScores, playerId, setNumber) {
  return (setScores || []).find(
    (score) =>
      score.player_id === playerId &&
      score.set_number === setNumber
  );
}

function SetScore({ score, currentSet }) {
  if (!score) {
    return (
      <span
        className={
          currentSet
            ? "tennis-set-score-empty current"
            : "tennis-set-score-empty"
        }
      >
        -
      </span>
    );
  }

  return (
    <span
      className={[
        "tennis-set-score",
        score.is_winner ? "winner" : "",
        currentSet ? "current" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {score.games_won ?? 0}

      {score.tiebreak_points !== null &&
        score.tiebreak_points !== undefined && (
          <small>
            ({score.tiebreak_points})
          </small>
        )}
    </span>
  );
}

export default function TennisMatchDetail({
  matchId,
  tour,
  onBack,
}) {
  const [match, setMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadMatch() {
      try {
        const endpoint =
          tour === "SOFASCORE"
            ? `http://127.0.0.1:8000/tennis/live/${matchId}`
            : `http://127.0.0.1:8000/tennis/match/${tour}/${matchId}`;

        const response = await fetch(endpoint);

        if (!response.ok) {
          throw new Error(
            `Request failed with status ${response.status}`
          );
        }

        const data = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        if (!cancelled) {
          if (tour === "SOFASCORE") {
            setMatch(data.match);
          } else {
            setMatch(data);
          }

          setError("");
          setLoading(false);
        }
      } catch (requestError) {
        if (!cancelled) {
          console.error(
            "Tennis match request error:",
            requestError
          );

          setError(
            "Unable to load this tennis match."
          );

          setLoading(false);
        }
      }
    }

    loadMatch();

    const interval = setInterval(
      loadMatch,
      15000
    );

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [matchId, tour]);

  const isSofaScoreMatch =
    tour === "SOFASCORE";

  const setNumbers = useMemo(() => {
    if (isSofaScoreMatch) {
      if (!match?.sets?.length) {
        return [];
      }

      return match.sets
        .map((set) => set.set_number)
        .filter(
          (number) =>
            Number.isInteger(number) &&
            number > 0
        )
        .sort((a, b) => a - b);
    }

    if (!match?.set_scores?.length) {
      return [];
    }

    const numbers = match.set_scores
      .map((score) => score.set_number)
      .filter(
        (number) =>
          Number.isInteger(number) &&
          number > 0
      );

    return [...new Set(numbers)].sort(
      (a, b) => a - b
    );
  }, [match, isSofaScoreMatch]);

  if (loading) {
    return (
      <div className="tennis-detail-page">
        <button
          type="button"
          className="tennis-back-button"
          onClick={onBack}
        >
          ← Back
        </button>

        <div className="tennis-detail-loading">
          Loading match...
        </div>
      </div>
    );
  }

  if (error || !match) {
    return (
      <div className="tennis-detail-page">
        <button
          type="button"
          className="tennis-back-button"
          onClick={onBack}
        >
          ← Back
        </button>

        <div className="tennis-detail-error">
          {error || "Match not found."}
        </div>
      </div>
    );
  }

  /*
   * SofaScore match format
   */
  if (isSofaScoreMatch) {
    const homePlayer =
      match.home_player || {};

    const awayPlayer =
      match.away_player || {};

    const tournament =
      match.tournament || {};

    const status =
      match.status || {};

    const currentSet =
      match.current_set || {};

    const score =
      match.score || {};

    const live =
      match.is_live === true ||
      status.type === "inprogress";

    const playerOneName =
      homePlayer.name || "TBD";

    const playerTwoName =
      awayPlayer.name || "TBD";

    const leagueName =
      tournament.name ||
      "Tennis";

    const currentSetNumber =
      currentSet.number || null;

    /*
     * Current game / tiebreak information
     */
    const currentHomePoints =
      score.home_points ??
      score.current_game_points?.home ??
      "";

    const currentAwayPoints =
      score.away_points ??
      score.current_game_points?.away ??
      "";

    const currentHomeGames =
      currentSet.home_games ?? 0;

    const currentAwayGames =
      currentSet.away_games ?? 0;

    const isTiebreak =
      currentSetNumber !== null &&
      currentHomeGames === 6 &&
      currentAwayGames === 6;

    const hasCurrentPoints =
      currentHomePoints !== "" ||
      currentAwayPoints !== "";

    return (
      <div className="tennis-detail-page">
        <button
          type="button"
          className="tennis-back-button"
          onClick={onBack}
        >
          ← Back to Tennis
        </button>

        <div className="tennis-detail-header">
          <div>
            <span className="section-label">
              {leagueName}
            </span>

            <h1>
              {playerOneName} vs {playerTwoName}
            </h1>

            <p>
              {tournament.ground_type ||
                match.ground_type ||
                "Surface unavailable"}
            </p>
          </div>

          <div
            className={`tennis-detail-status ${
              live ? "live" : ""
            }`}
          >
            {live ? (
              <>
                <span />
                LIVE
              </>
            ) : (
              status.description ||
              status.type ||
              "Scheduled"
            )}
          </div>
        </div>

        <div className="tennis-score-header">
          <div className="tennis-detail-player">
            <span>
              {playerOneName}
            </span>
          </div>

          <div className="tennis-detail-score">
            <strong>
              {score.home_sets ?? 0}
            </strong>

            <span>−</span>

            <strong>
              {score.away_sets ?? 0}
            </strong>
          </div>

          <div className="tennis-detail-player right">
            <span>
              {playerTwoName}
            </span>
          </div>
        </div>

        <div className="tennis-detail-score-description">
          Sets won
        </div>

        <div className="tennis-detail-meta">
          <span>
            {formatPhilippineDate(
              match.start_time
            )}
          </span>

          {currentSetNumber && (
            <span className="tennis-current-set">
              Set {currentSetNumber}
            </span>
          )}

          {live && (
            <span>
              {status.description || "Live"}
            </span>
          )}
        </div>

        {live && (
          <section className="tennis-current-game-section">
            <div className="tennis-detail-section-heading">
              <div>
                <span className="section-label">
                  Live Score
                </span>

                <h2>
                  {isTiebreak
                    ? "Current Tiebreak"
                    : "Current Game"}
                </h2>
              </div>

              <div className="tennis-detail-live-note">
                <span />
                LIVE
              </div>
            </div>

            <div className="tennis-current-game">
              <div className="tennis-current-game-player">
                <span>
                  {playerOneName}
                </span>

                <strong>
                  {hasCurrentPoints
                    ? currentHomePoints
                    : "-"}
                </strong>
              </div>

              <div className="tennis-current-game-separator">
                −
              </div>

              <div className="tennis-current-game-player right">
                <span>
                  {playerTwoName}
                </span>

                <strong>
                  {hasCurrentPoints
                    ? currentAwayPoints
                    : "-"}
                </strong>
              </div>
            </div>

            {currentSetNumber && (
              <div className="tennis-current-set-games">
  <span className="current-set-label">
    SET {currentSetNumber}
  </span>

  <strong className="current-set-score">
    {currentHomeGames}
    {" - "}
    {currentAwayGames}
  </strong>

  <span className="current-set-type">
    {isTiebreak
      ? "TIEBREAK"
      : "CURRENT GAMES"}
  </span>
</div>
            )}
          </section>
        )}

        <section className="tennis-scoreboard-section">
          <div className="tennis-detail-section-heading">
            <div>
              <span className="section-label">
                Scoreboard
              </span>

              <h2>Set Scores</h2>
            </div>

            {live && (
              <div className="tennis-detail-live-note">
                <span />
                Updating every 15 seconds
              </div>
            )}
          </div>

          {setNumbers.length > 0 ? (
            <div className="tennis-scoreboard-wrapper">
              <table className="tennis-scoreboard">
                <thead>
                  <tr>
                    <th>Player</th>

                    {setNumbers.map(
                      (setNumber) => (
                        <th
                          key={setNumber}
                          className={
                            currentSetNumber ===
                            setNumber
                              ? "current-set-header"
                              : ""
                          }
                        >
                          SET {setNumber}

                          {currentSetNumber ===
                            setNumber && (
                            <small>
                              LIVE
                            </small>
                          )}
                        </th>
                      )
                    )}

                    <th>Total</th>
                  </tr>
                </thead>

                <tbody>
                  <tr>
                    <td>
                      <span>
                        {playerOneName}
                      </span>
                    </td>

                    {setNumbers.map(
                      (setNumber) => {
                        const set =
                          match.sets?.find(
                            (item) =>
                              item.set_number ===
                              setNumber
                          );

                        const scoreValue =
                          set?.home_score;

                        return (
                          <td
                            key={setNumber}
                            className={
                              currentSetNumber ===
                              setNumber
                                ? "current-set-cell"
                                : ""
                            }
                          >
                            <SetScore
                              score={
                                scoreValue !==
                                  undefined &&
                                scoreValue !==
                                  null
                                  ? {
                                      games_won:
                                        scoreValue,
                                    }
                                  : null
                              }
                              currentSet={
                                currentSetNumber ===
                                setNumber
                              }
                            />
                          </td>
                        );
                      }
                    )}

                    <td className="total-score">
                      {score.home_sets ?? 0}
                    </td>
                  </tr>

                  <tr>
                    <td>
                      <span>
                        {playerTwoName}
                      </span>
                    </td>

                    {setNumbers.map(
                      (setNumber) => {
                        const set =
                          match.sets?.find(
                            (item) =>
                              item.set_number ===
                              setNumber
                          );

                        const scoreValue =
                          set?.away_score;

                        return (
                          <td
                            key={setNumber}
                            className={
                              currentSetNumber ===
                              setNumber
                                ? "current-set-cell"
                                : ""
                            }
                          >
                            <SetScore
                              score={
                                scoreValue !==
                                  undefined &&
                                scoreValue !==
                                  null
                                  ? {
                                      games_won:
                                        scoreValue,
                                    }
                                  : null
                              }
                              currentSet={
                                currentSetNumber ===
                                setNumber
                              }
                            />
                          </td>
                        );
                      }
                    )}

                    <td className="total-score">
                      {score.away_sets ?? 0}
                    </td>
                  </tr>
                </tbody>
              </table>

              <div className="tennis-scoreboard-note">
                Set scores show games won
                in each set.
              </div>
            </div>
          ) : (
            <div className="tennis-no-set-data">
              Set scores are not available
              yet.
            </div>
          )}
        </section>

                {live &&
          Array.isArray(match.live_updates) &&
          match.live_updates.length > 0 && (
            <section className="tennis-live-history-section">
              <div className="tennis-detail-section-heading">
                <div>
                  <span className="section-label">
                    Match Tracking
                  </span>

                  <h2>Live Score History</h2>
                </div>

                <div className="tennis-history-count">
                  {match.live_updates.length} updates
                </div>
              </div>

              <div className="tennis-live-history">
                {match.live_updates
                  .slice()
                  .reverse()
                  .map((update, index) => {
                    const recordedAt =
                      update.recorded_at
                        ? new Date(update.recorded_at)
                        : null;

                    const time =
                      recordedAt &&
                      !Number.isNaN(
                        recordedAt.getTime()
                      )
                        ? new Intl.DateTimeFormat(
                            "en-PH",
                            {
                              timeZone:
                                "Asia/Manila",
                              hour: "numeric",
                              minute: "2-digit",
                              second: "2-digit",
                            }
                          ).format(recordedAt)
                        : "--";

                    const updateSet =
                      update.current_set_number ??
                      "-";

                    const homeGames =
                      update.current_set?.home_games ??
                      "-";

                    const awayGames =
                      update.current_set?.away_games ??
                      "-";

                    const homePoints =
                      update.score?.home_points ??
                      "-";

                    const awayPoints =
                      update.score?.away_points ??
                      "-";

                    const isLatest =
                      index === 0;

                    return (
                      <div
                        key={`${update.recorded_at}-${index}`}
                        className={[
                          "tennis-history-row",
                          isLatest
                            ? "latest"
                            : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      >
                        <div className="tennis-history-time">
                          {time}

                          {isLatest && (
                            <span>
                              LATEST
                            </span>
                          )}
                        </div>

                        <div className="tennis-history-set">
                          <small>SET</small>
                          <strong>
                            {updateSet}
                          </strong>
                        </div>

                        <div className="tennis-history-games">
                          <small>GAMES</small>
                          <strong>
                            {homeGames} - {awayGames}
                          </strong>
                        </div>

                        <div className="tennis-history-points">
                          <small>POINTS</small>
                          <strong>
                            {homePoints} -{" "}
                            {awayPoints}
                          </strong>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </section>
          )}

        <section className="tennis-match-information">
          <div>
            <span>TOURNAMENT</span>

            <strong>
              {leagueName}
            </strong>
          </div>

          <div>
            <span>SURFACE</span>

            <strong>
              {match.ground_type ||
                tournament.ground_type ||
                "Unavailable"}
            </strong>
          </div>

          <div>
            <span>ROUND</span>

            <strong>
              {match.round?.name ||
                "Unavailable"}
            </strong>
          </div>

          <div>
            <span>STATUS</span>

            <strong>
              {status.description ||
                status.type ||
                "Scheduled"}
            </strong>
          </div>
        </section>
      </div>
    );
  }

  /*
   * Old ATP / WTA match format
   */
  const playerOne = getPlayer(match, 1);
  const playerTwo = getPlayer(match, 2);

  const playerOneName =
    playerOne?.player_name || "TBD";

  const playerTwoName =
    playerTwo?.player_name || "TBD";

  const playerOneIsWinner =
    playerOne?.result === "winner";

  const playerTwoIsWinner =
    playerTwo?.result === "winner";

  const live = isLiveMatch(match.status);

  const leagueName =
    String(
      match.league || tour || "Tennis"
    ).toUpperCase();

  const leagueLabel =
    leagueName === "WTA"
      ? "WTA Tennis"
      : leagueName === "ATP"
        ? "ATP Tennis"
        : `${leagueName} Tennis`;

  const currentSet =
    live &&
    Number.isInteger(match.current_period)
      ? match.current_period
      : null;

  return (
    <div className="tennis-detail-page">
      <button
        type="button"
        className="tennis-back-button"
        onClick={onBack}
      >
        ← Back to Tennis
      </button>

      <div className="tennis-detail-header">
        <div>
          <span className="section-label">
            {leagueLabel}
          </span>

          <h1>
            {playerOneName} vs {playerTwoName}
          </h1>

          <p>
            {match.venue ||
              "Venue unavailable"}
          </p>
        </div>

        <div
          className={`tennis-detail-status ${
            live ? "live" : ""
          }`}
        >
          {live ? (
            <>
              <span />
              LIVE
            </>
          ) : (
            match.status || "Scheduled"
          )}
        </div>
      </div>

      <div className="tennis-score-header">
        <div className="tennis-detail-player">
          <span
            className={
              playerOneIsWinner
                ? "winner"
                : ""
            }
          >
            {playerOneName}
          </span>

          {playerOneIsWinner && (
            <small>WINNER</small>
          )}
        </div>

        <div className="tennis-detail-score">
          <strong>
            {match.player_one_score ?? 0}
          </strong>

          <span>−</span>

          <strong>
            {match.player_two_score ?? 0}
          </strong>
        </div>

        <div className="tennis-detail-player right">
          <span
            className={
              playerTwoIsWinner
                ? "winner"
                : ""
            }
          >
            {playerTwoName}
          </span>

          {playerTwoIsWinner && (
            <small>WINNER</small>
          )}
        </div>
      </div>

      <div className="tennis-detail-score-description">
        Sets won
      </div>

      <div className="tennis-detail-meta">
        <span>
          {formatPhilippineDate(
            match.scheduled_at
          )}
        </span>

        {currentSet && (
          <span className="tennis-current-set">
            {live
              ? `Set ${currentSet}`
              : `${currentSet} sets`}
          </span>
        )}

        {live && match.game_clock && (
          <span>
            {match.game_clock}
          </span>
        )}
      </div>

      <section className="tennis-scoreboard-section">
        <div className="tennis-detail-section-heading">
          <div>
            <span className="section-label">
              Scoreboard
            </span>

            <h2>Set Scores</h2>
          </div>

          {live && (
            <div className="tennis-detail-live-note">
              <span />
              Updating every 15 seconds
            </div>
          )}
        </div>

        {setNumbers.length > 0 ? (
          <div className="tennis-scoreboard-wrapper">
            <table className="tennis-scoreboard">
              <thead>
                <tr>
                  <th>Player</th>

                  {setNumbers.map(
                    (setNumber) => (
                      <th
                        key={setNumber}
                        className={
                          currentSet ===
                          setNumber
                            ? "current-set-header"
                            : ""
                        }
                      >
                        SET {setNumber}

                        {currentSet ===
                          setNumber && (
                          <small>
                            LIVE
                          </small>
                        )}
                      </th>
                    )
                  )}

                  <th>Total</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  className={
                    playerOneIsWinner
                      ? "winner-row"
                      : ""
                  }
                >
                  <td>
                    <span>
                      {playerOneName}
                    </span>

                    {playerOneIsWinner && (
                      <small>W</small>
                    )}
                  </td>

                  {setNumbers.map(
                    (setNumber) => (
                      <td
                        key={setNumber}
                        className={
                          currentSet ===
                          setNumber
                            ? "current-set-cell"
                            : ""
                        }
                      >
                        <SetScore
                          score={getPlayerSetScore(
                            match.set_scores,
                            playerOne?.player_id,
                            setNumber
                          )}
                          currentSet={
                            currentSet ===
                            setNumber
                          }
                        />
                      </td>
                    )
                  )}

                  <td className="total-score">
                    {match.player_one_score ??
                      0}
                  </td>
                </tr>

                <tr
                  className={
                    playerTwoIsWinner
                      ? "winner-row"
                      : ""
                  }
                >
                  <td>
                    <span>
                      {playerTwoName}
                    </span>

                    {playerTwoIsWinner && (
                      <small>W</small>
                    )}
                  </td>

                  {setNumbers.map(
                    (setNumber) => (
                      <td
                        key={setNumber}
                        className={
                          currentSet ===
                          setNumber
                            ? "current-set-cell"
                            : ""
                        }
                      >
                        <SetScore
                          score={getPlayerSetScore(
                            match.set_scores,
                            playerTwo?.player_id,
                            setNumber
                          )}
                          currentSet={
                            currentSet ===
                            setNumber
                          }
                        />
                      </td>
                    )
                  )}

                  <td className="total-score">
                    {match.player_two_score ??
                      0}
                  </td>
                </tr>
              </tbody>
            </table>

            <div className="tennis-scoreboard-note">
              Set scores show games won in
              each set. Tiebreak points are
              shown in parentheses.
            </div>
          </div>
        ) : (
          <div className="tennis-no-set-data">
            Set scores are not available yet.
          </div>
        )}
      </section>

      <section className="tennis-match-information">
        <div>
          <span>TOUR</span>

          <strong>
            {leagueName}
          </strong>
        </div>

        <div>
          <span>VENUE</span>

          <strong>
            {match.venue ||
              "Venue unavailable"}
          </strong>
        </div>

        <div>
          <span>STATUS</span>

          <strong>
            {match.status ||
              "Scheduled"}
          </strong>
        </div>
      </section>
    </div>
  );
}