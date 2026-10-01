import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

function parseDate(dateValue) {
  if (!dateValue) {
    return null;
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date;
}

function getMatchStartTime(match) {
  return (
    match?.scheduled_at ||
    match?.start_time ||
    match?.sofascore?.start_time ||
    null
  );
}

function getPhilippineDateKey(dateValue) {
  if (!dateValue) {
    return null;
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  const parts = new Intl.DateTimeFormat("en-PH", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);

  const year = parts.find(
    (part) => part.type === "year"
  )?.value;

  const month = parts.find(
    (part) => part.type === "month"
  )?.value;

  const day = parts.find(
    (part) => part.type === "day"
  )?.value;

  if (!year || !month || !day) {
    return null;
  }

  return `${year}-${month}-${day}`;
}

function getTodayPhilippineDateKey() {
  return getPhilippineDateKey(new Date());
}

function getMatchStatusValue(match) {
  const status = match?.status;

  /*
   * Old API format:
   *
   * status: "Scheduled"
   */
  if (typeof status === "string") {
    return status.toLowerCase();
  }

  /*
   * SofaScore format:
   *
   * status: {
   *   type: "finished",
   *   description: "Ended"
   * }
   */
  if (status && typeof status === "object") {
    return String(
      status.type ||
        status.description ||
        ""
    ).toLowerCase();
  }

  return "";
}

function getMatchCategory(match) {
  const status = getMatchStatusValue(match);

  /*
   * LIVE
   */
  if (
    status.includes("live") ||
    status.includes("progress") ||
    status.includes("in progress") ||
    status.includes("halftime") ||
    status === "inprogress"
  ) {
    return "live";
  }

  /*
   * COMPLETED
   *
   * This covers both the old API and
   * SofaScore's "finished" status.
   */
  if (
    status === "final" ||
    status === "finished" ||
    status === "completed" ||
    status === "complete" ||
    status === "post" ||
    status === "ended"
  ) {
    return "completed";
  }

  return "scheduled";
}

function getPlayer(match, order) {
  /*
   * Old format
   */
  const players = Array.isArray(
    match?.players
  )
    ? match.players
    : [];

  const oldPlayer = players.find(
    (player) =>
      Number(
        player.participant_order
      ) === order
  );

  if (oldPlayer) {
    return oldPlayer;
  }

  /*
   * SofaScore format
   */
  if (order === 1) {
    return match?.home_player || null;
  }

  if (order === 2) {
    return match?.away_player || null;
  }

  return null;
}

function isSofaScoreMatch(match) {
  if (!match) {
    return false;
  }

  if (
    String(match.source || "").toLowerCase() ===
    "sofascore"
  ) {
    return true;
  }

  if (
    match.sofascore_event_id !== null &&
    match.sofascore_event_id !== undefined
  ) {
    return true;
  }

  if (match.sofascore) {
    return true;
  }

  return false;
}

function getPlayerName(match, order) {
  const player = getPlayer(
    match,
    order
  );

  if (!player) {
    return "";
  }

  return (
    player.player_name ||
    player.name ||
    player.short_name ||
    ""
  );
}

function getPlayerResult(match, order) {
  const player = getPlayer(
    match,
    order
  );

  if (!player) {
    return null;
  }

  if (player.result) {
    return player.result;
  }

  /*
   * SofaScore uses winnerCode:
   *
   * 1 = home winner
   * 2 = away winner
   */
  const winnerCode =
    match?.winnerCode ??
    match?.sofascore?.winnerCode;

  if (
    order === 1 &&
    Number(winnerCode) === 1
  ) {
    return "winner";
  }

  if (
    order === 2 &&
    Number(winnerCode) === 2
  ) {
    return "winner";
  }

  return null;
}

function hasValidPlayers(match) {
  const playerOne =
    getPlayerName(match, 1);

  const playerTwo =
    getPlayerName(match, 2);

  if (!playerOne || !playerTwo) {
    return false;
  }

  const invalidNames = new Set([
    "tbd",
    "to be determined",
    "unknown",
    "null",
    "undefined",
  ]);

  if (
    invalidNames.has(
      playerOne.trim().toLowerCase()
    )
  ) {
    return false;
  }

  if (
    invalidNames.has(
      playerTwo.trim().toLowerCase()
    )
  ) {
    return false;
  }

  return true;
}

function isInvalidCompletedMatch(match) {
  if (!hasValidPlayers(match)) {
    return true;
  }

  const playerOneScore =
    Number(
      match.player_one_score ??
        match.score?.home_sets ??
        0
    );

  const playerTwoScore =
    Number(
      match.player_two_score ??
        match.score?.away_sets ??
        0
    );

  /*
   * Do not display a completed match
   * that has a broken 0-0 result.
   */
  if (
    playerOneScore === 0 &&
    playerTwoScore === 0
  ) {
    return true;
  }

  return false;
}

/*
 * Convert the SofaScore live response into
 * the format our existing tennis card uses.
 */
function normalizeLiveMatch(match) {
  return {
    id: match.id,

    source: "sofascore",

    sofascore_event_id:
      match.sofascore_event_id ??
      match.sofascore?.sofascore_event_id ??
      null,

    league:
      match.tournament?.category ||
      match.tournament?.name ||
      "Tennis",

    venue:
      match.ground_type ||
      match.tournament?.ground_type ||
      "Venue unavailable",

    status: "LIVE",

    scheduled_at: match.start_time,

    current_period:
      match.current_set?.number || null,

    current_game_clock: null,

    player_one_score:
      match.score?.home_sets ?? 0,

    player_two_score:
      match.score?.away_sets ?? 0,

    current_home_points:
      match.score?.home_points || "",

    current_away_points:
      match.score?.away_points || "",

    players: [
      {
        participant_order: 1,
        player_id:
          match.home_player?.id,
        player_name:
          match.home_player?.name || "",
        result: null,
      },
      {
        participant_order: 2,
        player_id:
          match.away_player?.id,
        player_name:
          match.away_player?.name || "",
        result: null,
      },
    ],

    sofascore: match,
  };
}

function TennisMatchCard({
  match,
  onSelect,
  tour,
}) {

  const matchStartTime =
  getMatchStartTime(match);

  const isSofaScore =
    isSofaScoreMatch(match);

  const matchTour = isSofaScore
    ? "SOFASCORE"
    : tour;

  const category =
    getMatchCategory(match);

  const playerOne =
    getPlayerName(match, 1);

  const playerTwo =
    getPlayerName(match, 2);

  const playerOneResult =
    getPlayerResult(match, 1);

  const playerTwoResult =
    getPlayerResult(match, 2);

  const playerOneScore =
  match.player_one_score ??
  match.score?.home_sets ??
  0;

const playerTwoScore =
  match.player_two_score ??
  match.score?.away_sets ??
  0;

  const isFinal =
    category === "completed";

  const isLive =
    category === "live";

  const currentSet =
  match.current_period ??
  match.current_set?.number ??
  null;

  /*
   * Get the tournament/category label.
   *
   * Examples:
   * ATP
   * WTA
   * Challenger
   * ITF
   * Grand Slam
   */
  function getTournamentLabel() {
    const league = String(
      match.league || ""
    ).toLowerCase();

    if (league.includes("wta")) {
      return "WTA";
    }

    if (
      league.includes("challenger")
    ) {
      return "Challenger";
    }

    if (
      league.includes("itf")
    ) {
      return "ITF";
    }

    if (
      league.includes("atp")
    ) {
      return "ATP";
    }

    if (
      league.includes("grand slam")
    ) {
      return "Grand Slam";
    }

    return (
      match.league ||
      "Tennis"
    );
  }

  /*
   * Get the court/surface line.
   */
  function getCourtLabel() {
    if (
      match.venue &&
      match.venue !==
        "Venue unavailable"
    ) {
      return match.venue;
    }

    if (
      match.ground_type
    ) {
      return match.ground_type;
    }

    if (
      match.tournament?.ground_type
    ) {
      return match.tournament.ground_type;
    }

    return "Court unavailable";
  }

  /*
   * Format date in Philippine time.
   */
  function formatDatePH(value) {
    if (!value) {
      return "Date unavailable";
    }

    const date = new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return "Date unavailable";
    }

    return new Intl.DateTimeFormat(
      "en-PH",
      {
        timeZone:
          "Asia/Manila",
        month: "short",
        day: "numeric",
        year: "numeric",
      }
    ).format(date);
  }

  /*
   * Format Philippine time.
   */
  function formatTimePH(value) {
    if (!value) {
      return "TBD";
    }

    const date = new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return "TBD";
    }

    return new Intl.DateTimeFormat(
      "en-PH",
      {
        timeZone:
          "Asia/Manila",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }
    ).format(date);
  }

  /*
   * Format United States Eastern Time.
   */
  function formatTimeUS(value) {
    if (!value) {
      return "TBD";
    }

    const date = new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return "TBD";
    }

    return new Intl.DateTimeFormat(
      "en-US",
      {
        timeZone:
          "America/New_York",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }
    ).format(date);
  }

  /*
   * Status text.
   */
  function getStatusText() {
    if (isLive) {
      return "LIVE";
    }

    if (isFinal) {
      return "FINAL";
    }

    return formatTimePH(
      matchStartTime
    );
  }

  /*
   * Current tennis game score.
   *
   * Examples:
   * 15 - 30
   * 30 - 40
   * AD - 40
   */
  const hasCurrentGameScore =
    isLive &&
    match.current_home_points !==
      null &&
    match.current_home_points !==
      undefined &&
    match.current_home_points !==
      "" &&
    match.current_away_points !==
      null &&
    match.current_away_points !==
      undefined &&
    match.current_away_points !==
      "";

  const currentGameScore =
    hasCurrentGameScore
      ? `${match.current_home_points} - ${match.current_away_points}`
      : null;

  const setLabel =
    currentSet
      ? `Set ${currentSet}`
      : null;

  return (
    <button
      type="button"
      className={`tennis-match-card ${
        isLive
          ? "tennis-card-live"
          : isFinal
            ? "tennis-card-final"
            : "tennis-card-upcoming"
      }`}
      onClick={() =>
        onSelect(
          isSofaScore
            ? match.sofascore_event_id
            : match.id,
          matchTour
        )
      }
    >
      {/* TOP */}
      <div className="tennis-match-card-top">
        <div className="tennis-match-card-status">
          <span
            className={`tennis-status-dot ${
              isLive
                ? "live"
                : isFinal
                  ? "final"
                  : "scheduled"
            }`}
          />

          <span
            className={`tennis-match-status ${
              isLive
                ? "live"
                : isFinal
                  ? "final"
                  : "scheduled"
            }`}
          >
            {getStatusText()}
          </span>
        </div>

        <span className="tennis-match-category">
          {getTournamentLabel()}
        </span>
      </div>

      {/* TOURNAMENT / COURT */}
      <div className="tennis-match-location">
        <span className="tennis-match-tournament">
          {match.sofascore?.tournament?.name ||
            match.tournament?.name ||
            match.league ||
            "Tennis"}
        </span>

        <span className="tennis-match-venue">
          {getCourtLabel()}
        </span>
      </div>

      {/* PLAYERS + SET SCORE */}
      <div className="tennis-match-main">
        <div className="tennis-match-players">
          <div className="tennis-player-row">
            <div
              className={`tennis-player-name ${
                playerOneResult ===
                "winner"
                  ? "tennis-winner"
                  : ""
              }`}
            >
              <span>
                {playerOne}
              </span>

              {playerOneResult ===
                "winner" && (
                <span className="tennis-result-dot">
                  W
                </span>
              )}
            </div>
          </div>

          <div className="tennis-player-row">
            <div
              className={`tennis-player-name ${
                playerTwoResult ===
                "winner"
                  ? "tennis-winner"
                  : ""
              }`}
            >
              <span>
                {playerTwo}
              </span>

              {playerTwoResult ===
                "winner" && (
                <span className="tennis-result-dot">
                  W
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="tennis-match-score-area">
          <div className="tennis-match-set-score">
            {isFinal || isLive
              ? `${playerOneScore} - ${playerTwoScore}`
              : "-"}
          </div>

          {isLive && (
            <div className="tennis-match-current">
              {setLabel && (
                <span className="tennis-current-set">
                  {setLabel}
                </span>
              )}

              {currentGameScore && (
                <span className="tennis-current-game">
                  {currentGameScore}
                </span>
              )}
            </div>
          )}

          {isFinal && (
            <div className="tennis-match-current tennis-final-label">
              Final
            </div>
          )}
        </div>
      </div>

      {/* BOTTOM */}
      <div className="tennis-match-card-bottom">
        <div className="tennis-match-date">
  {formatDatePH(
    matchStartTime
  )}
</div>

<div className="tennis-match-times">
  <span className="tennis-time-ph">
    PH {formatTimePH(
      matchStartTime
    )}
  </span>

  <span className="tennis-time-us">
    US {formatTimeUS(
      matchStartTime
    )} ET
  </span>

  <span className="tennis-time-arrow">
    →
  </span>
</div>
      </div>
    </button>
  );
}

function TennisSection({
  label,
  title,
  matches,
  onSelect,
  tour,
}) {
  const carouselRef = useRef(null);

  if (matches.length === 0) {
    return null;
  }

  const scrollCarousel = (direction) => {
    if (!carouselRef.current) {
      return;
    }

    const amount =
      carouselRef.current.clientWidth * 0.85;

    carouselRef.current.scrollBy({
      left:
        direction === "next"
          ? amount
          : -amount,
      behavior: "smooth",
    });
  };

  return (
    <section className="tennis-section">
      <div className="tennis-section-heading">
        <div>
          <span className="section-label">
            {label}
          </span>

          <h2>{title}</h2>
        </div>

        {matches.length > 1 && (
          <div className="tennis-carousel-controls">
            <button
              type="button"
              onClick={() =>
                scrollCarousel("previous")
              }
              aria-label={`Previous ${title}`}
            >
              ‹
            </button>

            <button
              type="button"
              onClick={() =>
                scrollCarousel("next")
              }
              aria-label={`Next ${title}`}
            >
              ›
            </button>
          </div>
        )}
      </div>

      <div
        ref={carouselRef}
        className="tennis-match-grid"
      >
        {matches.map((match) => (
          <TennisMatchCard
            key={`${
              isSofaScoreMatch(match)
                ? "sofascore"
                : "legacy"
            }-${match.id}`}
            match={match}
            onSelect={onSelect}
            tour={
              isSofaScoreMatch(match)
                ? "SOFASCORE"
                : tour
            }
          />
        ))}
      </div>
    </section>
  );
}

export default function Tennis({
  onSelectMatch,
}) {
  const [tour, setTour] =
    useState("ATP");

  const [matches, setMatches] =
    useState([]);

  const [liveMatches, setLiveMatches] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadMatches() {
      try {
        const [
          matchResponse,
          liveResponse,
        ] = await Promise.all([
          fetch(
            `http://127.0.0.1:8000/tennis/matches/${tour}`
          ),
          fetch(
            "http://127.0.0.1:8000/tennis/live"
          ),
        ]);

        if (!matchResponse.ok) {
          throw new Error(
            `Tennis request failed with status ${matchResponse.status}`
          );
        }

        if (!liveResponse.ok) {
          throw new Error(
            `Live tennis request failed with status ${liveResponse.status}`
          );
        }

        const matchData =
          await matchResponse.json();

        const liveData =
          await liveResponse.json();

        if (cancelled) {
          return;
        }

        if (matchData.error) {
          throw new Error(
            matchData.error
          );
        }

        if (liveData.error) {
          throw new Error(
            liveData.error
          );
        }

        const allMatches =
          Array.isArray(matchData)
            ? matchData
            : [];

        const sofaLiveMatches =
          Array.isArray(
            liveData.matches
          )
            ? liveData.matches
                .map(
                  normalizeLiveMatch
                )
                .filter(
                  hasValidPlayers
                )
            : [];

        /*
         * The /tennis/matches/{tour}
         * endpoint contains the legacy
         * matches and SofaScore
         * completed/upcoming matches.
         *
         * Remove live legacy records because
         * SofaScore is the live source.
         */
        const nonLiveMatches =
          allMatches.filter(
            (match) =>
              getMatchCategory(
                match
              ) !== "live"
          );

        setMatches(
          nonLiveMatches
        );

        setLiveMatches(
          sofaLiveMatches
        );

        setError("");
        setLoading(false);
      } catch (requestError) {
        if (!cancelled) {
          console.error(
            "Tennis request error:",
            requestError
          );

          setError(
            `Unable to load ${tour} matches.`
          );

          setLoading(false);
        }
      }
    }

    setLoading(true);
    setError("");

    loadMatches();

    const interval =
      setInterval(
        loadMatches,
        30000
      );

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [tour]);

const categorizedMatches = useMemo(() => {
  const today = [];
  const completed = [];
  const upcoming = [];

  const todayKey =
    getTodayPhilippineDateKey();

  for (const match of matches) {
    /*
     * Never show matches where the
     * players are missing or TBD.
     */
    if (!hasValidPlayers(match)) {
      continue;
    }

    const category =
      getMatchCategory(match);

    const matchStartTime =
      getMatchStartTime(match);

    /*
     * COMPLETED
     */
    if (category === "completed") {
      if (
        isInvalidCompletedMatch(match)
      ) {
        continue;
      }

      completed.push(match);
      continue;
    }

    /*
     * TODAY / UPCOMING
     */
    const matchDate =
      getPhilippineDateKey(
        matchStartTime
      );

    if (!matchDate) {
      continue;
    }

    /*
     * Today's scheduled matches
     */
    if (matchDate === todayKey) {
      today.push(match);
      continue;
    }

    /*
     * Future scheduled matches
     */
    if (matchDate > todayKey) {
      upcoming.push(match);
    }
  }

  /*
   * TODAY
   * Earliest first
   */
  today.sort((a, b) => {
    const aTime = getMatchStartTime(a);
    const bTime = getMatchStartTime(b);

    return (
      new Date(aTime) -
      new Date(bTime)
    );
  });

  /*
   * COMPLETED
   * Most recent first
   */
  completed.sort((a, b) => {
    const aTime = getMatchStartTime(a);
    const bTime = getMatchStartTime(b);

    return (
      new Date(bTime) -
      new Date(aTime)
    );
  });

  /*
   * UPCOMING
   * Earliest first
   */
  upcoming.sort((a, b) => {
    const aTime = getMatchStartTime(a);
    const bTime = getMatchStartTime(b);

    return (
      new Date(aTime) -
      new Date(bTime)
    );
  });

  /*
   * LIVE
   */
  const sortedLive =
    [...liveMatches].sort(
      (a, b) => {
        const aTime =
          getMatchStartTime(a);

        const bTime =
          getMatchStartTime(b);

        return (
          new Date(aTime) -
          new Date(bTime)
        );
      }
    );

  return {
    live: sortedLive,
    today,
    completed,
    upcoming,
  };
}, [
  matches,
  liveMatches,
]);

const hasAnyMatches =
  categorizedMatches.live.length >
    0 ||
  categorizedMatches.today.length >
    0 ||
  categorizedMatches.completed.length >
    0 ||
  categorizedMatches.upcoming.length >
    0;

  return (
    <div className="tennis-page">
      <div className="tennis-page-header">
        <div>
          <span className="section-label">
            Tennis
          </span>

          <h1>
            {tour} Tennis
          </h1>

          <p>
            Live scores, completed matches,
            and upcoming {tour} fixtures.
          </p>
        </div>

        <div className="tennis-live-indicator">
          <span />
          Live updates every 30 seconds
        </div>
      </div>

      <div className="tennis-tour-tabs">
        <button
          type="button"
          className={
            tour === "ATP"
              ? "active"
              : ""
          }
          onClick={() =>
            setTour("ATP")
          }
        >
          ATP
        </button>

        <button
          type="button"
          className={
            tour === "WTA"
              ? "active"
              : ""
          }
          onClick={() =>
            setTour("WTA")
          }
        >
          WTA
        </button>
      </div>

      {loading ? (
        <div className="tennis-loading">
          Loading {tour} matches...
        </div>
      ) : error ? (
        <div className="tennis-error">
          {error}
        </div>
      ) : (
        <>
          <TennisSection
            label="Live"
            title="Live Matches"
            matches={
              categorizedMatches.live
            }
            onSelect={onSelectMatch}
            tour="SOFASCORE"
          />

          <TennisSection
            label="Today"
            title="Today's Matches"
            matches={
              categorizedMatches.today
            }
            onSelect={onSelectMatch}
            tour={tour}
          />

          <TennisSection
            label="Completed"
            title="Completed Matches"
            matches={
              categorizedMatches.completed
            }
            onSelect={onSelectMatch}
            tour={tour}
          />

          <TennisSection
            label="Upcoming"
            title="Upcoming Matches"
            matches={
              categorizedMatches.upcoming
            }
            onSelect={onSelectMatch}
            tour={tour}
          />

          {!hasAnyMatches && (
            <div className="tennis-empty">
              No {tour} matches are
              currently available.
            </div>
          )}
        </>
      )}
    </div>
  );
}