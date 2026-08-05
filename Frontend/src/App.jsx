import { useState, useEffect, useRef } from "react";
import "./App.css";

const API_BASE = "http://localhost:8001";

const STATUS_MESSAGES = [
  "Reading your request…",
  "Looking up matching flights…",
  "Checking hotel options…",
  "Putting together your itinerary…",
  "Finalizing your travel plan…",
];

// Turns the raw "Airline: X\nDeparture: Y\n..." text from the backend
// into structured flight objects for card rendering.
function parseFlights(text) {
  if (!text) return [];
  const blocks = text
    .split(/\n\s*\n/)
    .map((b) => b.trim())
    .filter(Boolean);

  return blocks
    .map((block) => {
      const get = (label) => {
        const match = block.match(new RegExp(`${label}:\\s*(.+)`));
        return match ? match[1].trim() : "";
      };
      const airline = get("Airline");
      if (!airline) return null;
      return {
        airline,
        departure: get("Departure"),
        arrival: get("Arrival"),
        stops: get("Stops"),
        price: get("Price"),
        status: get("Status"),
      };
    })
    .filter(Boolean);
}

// ---------- Lightweight markdown renderer (headings, bullets, bold, links) ----------
function boldFormat(str, keyBase) {
  const parts = str.split(/\*\*([^*]+)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={`${keyBase}-b-${i}`}>{part}</strong> : part
  );
}

function inlineFormat(str, keyBase) {
  const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s]+)/g;
  const out = [];
  let lastIndex = 0;
  let match;
  let key = 0;
  while ((match = linkRegex.exec(str)) !== null) {
    if (match.index > lastIndex) {
      out.push(...boldFormat(str.slice(lastIndex, match.index), `${keyBase}-${key++}`));
    }
    if (match[1] && match[2]) {
      out.push(
        <a key={`${keyBase}-link-${key++}`} href={match[2]} target="_blank" rel="noopener noreferrer" className="md-link">
          {match[1]}
        </a>
      );
    } else if (match[3]) {
      out.push(
        <a key={`${keyBase}-link-${key++}`} href={match[3]} target="_blank" rel="noopener noreferrer" className="md-link">
          {match[3]}
        </a>
      );
    }
    lastIndex = linkRegex.lastIndex;
  }
  if (lastIndex < str.length) {
    out.push(...boldFormat(str.slice(lastIndex), `${keyBase}-${key++}`));
  }
  return out;
}

function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split("\n");
  const elements = [];
  let listBuffer = [];

  const flushList = (key) => {
    if (listBuffer.length) {
      elements.push(
        <ul key={`ul-${key}`} className="md-list">
          {listBuffer.map((item, i) => (
            <li key={i}>{inlineFormat(item, `li-${key}-${i}`)}</li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList(idx);
      return;
    }
    if (trimmed.startsWith("### ")) {
      flushList(idx);
      elements.push(<h5 key={idx} className="md-h5">{inlineFormat(trimmed.slice(4), `h-${idx}`)}</h5>);
      return;
    }
    if (trimmed.startsWith("## ")) {
      flushList(idx);
      elements.push(<h4 key={idx} className="md-h4">{inlineFormat(trimmed.slice(3), `h-${idx}`)}</h4>);
      return;
    }
    if (trimmed.startsWith("# ")) {
      flushList(idx);
      elements.push(<h3 key={idx} className="md-h3">{inlineFormat(trimmed.slice(2), `h-${idx}`)}</h3>);
      return;
    }
    if (/^[-*]\s+/.test(trimmed)) {
      listBuffer.push(trimmed.replace(/^[-*]\s+/, ""));
      return;
    }
    flushList(idx);
    elements.push(<p key={idx} className="md-p">{inlineFormat(trimmed, `p-${idx}`)}</p>);
  });
  flushList("end");
  return elements;
}

const DESTINATIONS = [
  { name: "Tokyo", flag: "🇯🇵", img: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400&q=80", prompt: "7-day trip to Tokyo, Japan" },
  { name: "Paris", flag: "🇫🇷", img: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400&q=80", prompt: "Romantic 5-day Paris trip" },
  { name: "Bangkok", flag: "🇹🇭", img: "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=400&q=80", prompt: "Bangkok street food and temples trip" },
  { name: "Rome", flag: "🇮🇹", img: "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&q=80", prompt: "Historical 4-day Rome itinerary" },
  { name: "Dubai", flag: "🇦🇪", img: "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=400&q=80", prompt: "Dubai weekend luxury trip" },
];

const QUICK_PROMPTS = [
  "7-day Japan under ₹2L",
  "Paris trip for 5 days",
  "Dubai weekend trip",
  "Bali backpacking 10 days",
];

function FlightCard({ flight, skyscannerUrl }) {
  return (
    <div className="flight-card">
      <div className="flight-card-top">
        <span className="flight-airline">{flight.airline}</span>
        {flight.stops && <span className="flight-status neutral">{flight.stops}</span>}
      </div>
      <div className="flight-route">
        <div className="flight-point">
          <span className="flight-label">From</span>
          <span className="flight-value">{flight.departure || "—"}</span>
        </div>
        <span className="flight-arrow">✈️</span>
        <div className="flight-point">
          <span className="flight-label">To</span>
          <span className="flight-value">{flight.arrival || "—"}</span>
        </div>
        {flight.price && (
          <div className="flight-point flight-price-block">
            <span className="flight-label">Price</span>
            <span className="flight-price">{flight.price}</span>
          </div>
        )}
        {skyscannerUrl && (
          <a className="flight-select-btn" href={skyscannerUrl} target="_blank" rel="noopener noreferrer">
            Select
          </a>
        )}
      </div>
    </div>
  );
}

function ResultCard({ icon, title, children, actionLabel, actionUrl, markdown }) {
  return (
    <div className="result-card">
      <div className="result-card-head">
        <span className="result-icon">{icon}</span>
        <h3>{title}</h3>
        {actionUrl && (
          <a className="book-btn" href={actionUrl} target="_blank" rel="noopener noreferrer">
            {actionLabel} ↗
          </a>
        )}
      </div>
      {markdown ? (
        <div className="result-body md-body">{renderMarkdown(children)}</div>
      ) : (
        <pre className="result-body">{children}</pre>
      )}
    </div>
  );
}

const FEATURES = [
  {
    title: "Find Cheap Flights",
    desc: "AI scans flight deals and finds the lowest fares in seconds.",
    img: "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500&q=80",
  },
  {
    title: "Book the Best Hotels",
    desc: "Get hotel options tailored to your budget and style.",
    img: "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=500&q=80",
  },
  {
    title: "Generate Itineraries",
    desc: "One-click day-by-day travel schedules personalized for you.",
    img: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=500&q=80",
  },
  {
    title: "Save Time & Stress",
    desc: "Your AI trip planner for flights, hotels & itineraries.",
    img: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=500&q=80",
  },
];

const TESTIMONIALS = [
  {
    quote:
      "Planned my whole Delhi trip in minutes — flights, hotels, and a full itinerary, all in one chat. Saved me hours of tab-switching.",
    name: "Moin Ali",
    role: "Solo traveler",
  },
  {
    quote:
      "The flight search found options I hadn't seen anywhere else, and the hotel picks matched my budget perfectly. Genuinely stress-free planning.",
    name: "Aalam Ansari",
    role: "Weekend tripper",
  },
  {
    quote:
      "Loved how it broke down neighborhoods before suggesting hotels. Felt like having a local friend plan the trip for me.",
    name: "faisal khan",
    role: "First-time visitor",
  },
];

function Features() {
  return (
    <section className="features">
      <div className="features-grid">
        {FEATURES.map((f) => (
          <div key={f.title} className="feature-card">
            <img src={f.img} alt={f.title} />
            <div className="feature-card-body">
              <h4>{f.title}</h4>
              <p>{f.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Testimonials() {
  return (
    <section className="testimonials">
      <span className="section-tag">User Stories</span>
      <h2>Voices of Our Travelers</h2>
      <p className="testimonials-sub">
        See how this AI planner has helped travelers find affordable flights, book great
        hotels, and generate ready-to-use itineraries.
      </p>
      <div className="testimonial-track">
        {TESTIMONIALS.map((t) => (
          <div key={t.name} className="testimonial-card">
            <p>&ldquo;{t.quote}&rdquo;</p>
            <div className="testimonial-author">
              <span className="testimonial-avatar">{t.name[0]}</span>
              <div>
                <strong>{t.name}</strong>
                <span>{t.role}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// Simple inline SVG icons so no extra library is needed
function LinkedInIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.03-1.85-3.03-1.86 0-2.15 1.45-2.15 2.94v5.66H9.33V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45z" />
    </svg>
  );
}
function InstagramIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.16c3.2 0 3.58.01 4.85.07 3.25.15 4.77 1.69 4.92 4.92.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.15 3.23-1.66 4.77-4.92 4.92-1.27.06-1.64.07-4.85.07s-3.58-.01-4.85-.07c-3.26-.15-4.77-1.7-4.92-4.92-.06-1.27-.07-1.65-.07-4.85s.02-3.58.07-4.85c.15-3.23 1.67-4.77 4.92-4.92 1.27-.06 1.65-.07 4.85-.07zM12 0C8.74 0 8.33.01 7.05.07 2.7.27.27 2.69.07 7.05.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.2 4.36 2.62 6.78 6.98 6.98C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c4.35-.2 6.78-2.62 6.98-6.98.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95C23.73 2.7 21.3.27 16.95.07 15.67.01 15.26 0 12 0zm0 5.84A6.16 6.16 0 1 0 12 18.16 6.16 6.16 0 0 0 12 5.84zm0 10.16A4 4 0 1 1 12 8a4 4 0 0 1 0 8zm6.41-10.4a1.44 1.44 0 1 1 0-2.88 1.44 1.44 0 0 1 0 2.88z" />
    </svg>
  );
}
function MailIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z" />
    </svg>
  );
}

function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-brand-block">
          <span className="footer-brand">✈️ AI Travel Planner</span>
          <p>Plan flights, hotels, and itineraries in one place.</p>
        </div>

        <div className="footer-profile">
          <img src="/azam.jpg" alt="Azam Ali" className="footer-avatar" />
          <div>
            <p className="footer-built-by">Built by Azam Ali </p>
            <span className="footer-contact-heading">Contact Me</span>
            <div className="footer-social-icons">
              <a
                href="https://www.linkedin.com/in/azam-ali-38276a29a/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn"
                className="social-icon"
              >
                <LinkedInIcon />
              </a>
              <a
                href="https://www.instagram.com/azam_ansari57255/?hl=en"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
                className="social-icon"
              >
                <InstagramIcon />
              </a>
              <a href="mailto:azamansari57255@gmail.com" aria-label="Email" className="social-icon">
                <MailIcon />
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusIndex, setStatusIndex] = useState(0);
  const [history, setHistory] = useState([]);
  const statusTimer = useRef(null);

  useEffect(() => {
    if (loading) {
      setStatusIndex(0);
      statusTimer.current = setInterval(() => {
        setStatusIndex((i) => (i + 1 < STATUS_MESSAGES.length ? i + 1 : i));
      }, 1100);
    } else {
      clearInterval(statusTimer.current);
    }
    return () => clearInterval(statusTimer.current);
  }, [loading]);

  const runSearch = async (q) => {
    const finalQuery = q ?? query;
    if (!finalQuery.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);
    setQuery(finalQuery);

    try {
      const response = await fetch(`${API_BASE}/travel-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: finalQuery, thread_id: threadId }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Something went wrong");
      }

      const data = await response.json();
      setResult(data);
      setThreadId(data.thread_id);
      setHistory((h) => [{ id: `${Date.now()}`, query: finalQuery, result: data }, ...h]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    runSearch();
  };

  const loadHistoryItem = (item) => {
    setQuery(item.query);
    setResult(item.result);
    setError("");
  };

  const downloadAll = () => {
    if (!result) return;
    const content = `TRAVEL PLAN
Query: ${query}

=== FLIGHTS ===
${result.flight_results || "N/A"}

=== HOTELS ===
${result.hotel_results || "N/A"}

=== ITINERARY ===
${result.itinerary || "N/A"}

=== SUMMARY ===
${result.final_response || "N/A"}
`;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `travel-plan-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page">
      {/* ---------- HERO ---------- */}
      <section className="hero">
        <img
          className="hero-img"
          src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600&q=80"
          alt=""
        />
        <div className="hero-scrim" />
        <div className="hero-content">
          <span className="eyebrow">AI TRAVEL PLANNER</span>
          <h1>Where to, next?</h1>
          <p>Tell the agent your trip in plain words — flights, hotels, and a day-by-day plan, in one go.</p>
        </div>

        <form className="search-card" onSubmit={handleSubmit}>
          <div className="search-card-notch left" />
          <div className="search-card-notch right" />
          <span className="search-icon">✈️</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Plan a trip from Delhi to Mumbai for 3 days"
          />
          <button type="submit" disabled={loading}>
            {loading ? "Planning…" : "Plan Trip"}
          </button>
        </form>
      </section>

      {/* ---------- LAYOUT: SIDEBAR + CONTENT ---------- */}
      <div className="layout">
        <aside className="sidebar">
          <h4>🕘 History</h4>
          {history.length === 0 && <p className="sidebar-empty">Your past searches will show up here.</p>}
          <div className="sidebar-list">
            {history.map((h) => (
              <button
                key={h.id}
                className={`history-item ${result === h.result ? "active" : ""}`}
                onClick={() => loadHistoryItem(h)}
                type="button"
              >
                {h.query}
              </button>
            ))}
          </div>
        </aside>

        <main className="content">
          <section className="destinations">
            <div className="destinations-track">
              {DESTINATIONS.map((d) => (
                <button key={d.name} className="dest-card" onClick={() => runSearch(d.prompt)} type="button">
                  <img src={d.img} alt={d.name} />
                  <span className="dest-label">
                    {d.flag} {d.name}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="quick-prompts">
            <h4>📖 Describe your trip</h4>
            <div className="chip-row">
              {QUICK_PROMPTS.map((p) => (
                <button key={p} className="chip" onClick={() => runSearch(p)} type="button">
                  {p}
                </button>
              ))}
            </div>
          </section>

          {error && <div className="error-banner">⚠ {error}</div>}
          {loading && (
            <div className="loading-banner">
              <span className="spinner" />
              {STATUS_MESSAGES[statusIndex]}
            </div>
          )}

          {result && (
            <section className="results">
              <div className="result-card">
                <div className="result-card-head">
                  <span className="result-icon">✈️</span>
                  <h3>Flights</h3>
                  {result.skyscanner_url && (
                    <a className="book-btn" href={result.skyscanner_url} target="_blank" rel="noopener noreferrer">
                      Book on Skyscanner ↗
                    </a>
                  )}
                </div>
                {(() => {
                  const flights = parseFlights(result.flight_results);
                  if (flights.length === 0) {
                    return <pre className="result-body">{result.flight_results || "No flights found."}</pre>;
                  }
                  return (
                    <div className="flight-list">
                      {flights.map((f, i) => (
                        <FlightCard key={i} flight={f} skyscannerUrl={result.skyscanner_url} />
                      ))}
                      <p className="flight-note">
                        Live pricing isn't available from the current data source — showing schedule/status only.
                      </p>
                    </div>
                  );
                })()}
              </div>

              <ResultCard
                icon="🏨"
                title="Hotels"
                actionLabel="Book Hotel"
                actionUrl={result.booking_url}
                markdown
              >
                {result.hotel_results}
              </ResultCard>

              <ResultCard icon="🗓️" title="Itinerary" markdown>
                {result.itinerary}
              </ResultCard>

              <ResultCard icon="📋" title="Summary" markdown>
                {result.final_response}
              </ResultCard>

              <button className="download-all-btn" onClick={downloadAll} type="button">
                ⬇ Download Full Plan
              </button>
            </section>
          )}
        </main>
      </div>

      <Features />
      <Testimonials />
      <Footer />
    </div>
  );
}
