import {
  ArrowRightLeft,
  Dumbbell,
  Home,
  Menu,
  Newspaper,
  Search,
  Trophy,
  Volleyball,
  X,
} from "lucide-react";
import { useState } from "react";
import "./App.css";
import GameDetail from "./GameDetail";
import NBAGames from "./NBAGames";
import Tennis from "./Tennis";
import TennisMatchDetail from "./TennisMatchDetail";

function App() {
  const [activePage, setActivePage] = useState("Home");
  const [selectedGameId, setSelectedGameId] = useState(null);
  const [selectedTennisMatch, setSelectedTennisMatch] =
  useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    {
      name: "Home",
      icon: Home,
    },
    {
      name: "NBA",
      icon: Trophy,
    },
    {
      name: "Tennis",
      icon: Dumbbell,
    },
    {
      name: "UAAP Basketball",
      icon: Trophy,
    },
    {
      name: "UAAP Volleyball",
      icon: Volleyball,
    },
  ];

  const handleNavigation = (page) => {
  setActivePage(page);
  setSelectedGameId(null);
  setSelectedTennisMatch(null);
  setMobileMenuOpen(false);
};

  return (
    <div className="app">
      <header className="mobile-header">
        <button
          className="icon-button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Open menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <div className="mobile-logo">
          <span>Atletiks</span>
        </div>

        <button className="icon-button" aria-label="Search">
          <Search size={22} />
        </button>
      </header>

      <aside className={`sidebar ${mobileMenuOpen ? "open" : ""}`}>
        <div className="logo">
          <div className="logo-mark">A</div>
          <div>
            <h1>Atletiks</h1>
            <p>Sports Central</p>
          </div>
        </div>

        <nav className="navigation">
          <p className="navigation-title">MENU</p>

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                className={`nav-item ${
                  activePage === item.name ? "active" : ""
                }`}
                onClick={() => handleNavigation(item.name)}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <p>Atletiks</p>
          <span>Sports data and news</span>
        </div>
      </aside>

      <main className="main-content">
  {selectedGameId ? (
  <GameDetail
    matchId={selectedGameId}
    onBack={() => setSelectedGameId(null)}
  />
) : selectedTennisMatch ? (
  <TennisMatchDetail
    matchId={selectedTennisMatch.matchId}
    tour={selectedTennisMatch.tour}
    onBack={() =>
      setSelectedTennisMatch(null)
    }
  />
) : activePage === "NBA" ? (
  <NBAGames onSelectGame={setSelectedGameId} />
) : activePage === "Tennis" ? (
  <Tennis
  onSelectMatch={(matchId, tour) =>
    setSelectedTennisMatch({
      matchId,
      tour,
    })
  }
/>
) : (
  <>
      <div className="topbar">
          <div>
            <p className="page-label">SPORTS CENTRAL</p>
            <h2>{activePage}</h2>
          </div>

          <button className="search-button">
            <Search size={20} />
            <span>Search</span>
          </button>
        </div>

        <section className="hero">
          <div className="hero-content">
            <span className="hero-tag">YOUR SPORTS HUB</span>

            <h1>
              Stay updated with
              <br />
              <span>every game.</span>
            </h1>

            <p>
              Scores, news, transactions, results, and more from the sports
              you follow.
            </p>
          </div>
        </section>

        <section className="section">
          <div className="section-header">
            <div>
              <p className="section-label">LATEST</p>
              <h3>Today's Sports</h3>
            </div>

            <button className="view-all">
              View all
              <ArrowRightLeft size={16} />
            </button>
          </div>

          <div className="sports-grid">
            <div className="sport-card">
              <div className="sport-card-top">
                <div className="sport-icon nba">
                  <Trophy size={24} />
                </div>

                <span className="sport-label">NBA</span>
              </div>

              <h4>NBA</h4>
              <p>Scores, trades, free agents, signings, and headlines.</p>

              <div className="card-link">
                Explore NBA
                <span>→</span>
              </div>
            </div>

            <div className="sport-card">
              <div className="sport-card-top">
                <div className="sport-icon tennis">
                  <Dumbbell size={24} />
                </div>

                <span className="sport-label">TENNIS</span>
              </div>

              <h4>Tennis</h4>
              <p>Results, tournaments, players, and latest headlines.</p>

              <div className="card-link">
                Explore Tennis
                <span>→</span>
              </div>
            </div>

            <div className="sport-card">
              <div className="sport-card-top">
                <div className="sport-icon uaap">
                  <Trophy size={24} />
                </div>

                <span className="sport-label">UAAP</span>
              </div>

              <h4>UAAP Basketball</h4>
              <p>Scores, standings, transactions, and team news.</p>

              <div className="card-link">
                Explore UAAP
                <span>→</span>
              </div>
            </div>

            <div className="sport-card">
              <div className="sport-card-top">
                <div className="sport-icon volleyball">
                  <Volleyball size={24} />
                </div>

                <span className="sport-label">UAAP</span>
              </div>

              <h4>Women's Volleyball</h4>
              <p>Scores, standings, player movement, and news.</p>

              <div className="card-link">
                Explore Volleyball
                <span>→</span>
              </div>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="section-header">
            <div>
              <p className="section-label">UPDATES</p>
              <h3>Latest Headlines</h3>
            </div>
          </div>

          <div className="news-list">
            <div className="news-card">
              <div className="news-icon">
                <Newspaper size={22} />
              </div>

              <div className="news-content">
                <span>NBA</span>
                <h4>NBA news will appear here</h4>
                <p>
                  Our n8n workflows will collect the latest NBA headlines.
                </p>
              </div>

              <span className="news-arrow">→</span>
            </div>

            <div className="news-card">
              <div className="news-icon">
                <Newspaper size={22} />
              </div>

              <div className="news-content">
                <span>TENNIS</span>
                <h4>Tennis news will appear here</h4>
                <p>
                  Results and headlines will be added once our data pipeline
                  is connected.
                </p>
              </div>

              <span className="news-arrow">→</span>
            </div>

            <div className="news-card">
              <div className="news-icon">
                <Newspaper size={22} />
              </div>

              <div className="news-content">
                <span>UAAP</span>
                <h4>UAAP news will appear here</h4>
                <p>
                  UAAP basketball and volleyball updates will be collected
                  automatically.
                </p>
              </div>

              <span className="news-arrow">→</span>
            </div>
          </div>
                     </section>
    </>
  )}
</main>
    </div>
  );
}

export default App;