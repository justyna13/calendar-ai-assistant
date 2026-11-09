import Link from "next/link";
import ApiHealth from "@/app/components/ApiHealth";
import GoogleLoginStatus from "./components/GoogleLoginStatus";

const suggestions = [
  "Co mam w przyszłym tygodniu?",
  "Czy mam wolne w piątek po 17:00?",
  "Dodaj trening we wtorek o 18:00 na godzinę.",
];

export default function Home() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Calendar Copilot, strona główna">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </span>
          <span>Calendar Copilot</span>
        </Link>
        <div className="topbar-right">
          <span className="model-status flex gap-2">
            <GoogleLoginStatus />
            <span>|</span>
            <ApiHealth />
            <span>|</span>
            <span className="status-dot" />
            asystent kalendarza
          </span>
        </div>
      </header>

      <section className="chat-layout">
        <div className="welcome-view">
          <div className="welcome-orbit" aria-hidden="true">
            <div className="orbit-ring orbit-ring-outer" />
            <div className="orbit-ring orbit-ring-inner" />
            <div className="orbit-core">
              <span className="sparkle">✳</span>
            </div>
            <span className="orbit-dot orbit-dot-one" />
            <span className="orbit-dot orbit-dot-two" />
          </div>
          <p className="eyebrow">
            CALENDAR COPILOT <span /> TWÓJ KALENDARZ
          </p>
          <h1>
            Co masz
            <br />
            <em>w planach?</em>
          </h1>
          <p className="welcome-copy">Przeglądaj wydarzenia i planuj kolejne z pomocą asystenta.</p>
          <div className="suggestions" aria-label="Przykładowe pytania">
            {suggestions.map((suggestion, index) => (
              <div className="suggestion" key={suggestion}>
                <span className="suggestion-index">0{index + 1}</span>
                <span>{suggestion}</span>
                <span className="suggestion-arrow" aria-hidden="true">
                  ↗
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="composer-wrap">
          <div className="composer" aria-label="Pole wiadomości asystenta">
            <textarea
              aria-label="Wiadomość do asystenta"
              placeholder="Zapytaj o swój kalendarz..."
              rows={1}
              disabled
            />
            <button
              className="send-button"
              type="button"
              title="Wyślij wiadomość"
              aria-label="Wyślij wiadomość"
              disabled
            >
              <span className="send-icon" aria-hidden="true">
                ↑
              </span>
            </button>
          </div>
          <div className="composer-meta">
            <span>GOOGLE CALENDAR</span>
            <span className="meta-divider" />
            <span>WYMAGA POŁĄCZENIA</span>
          </div>
        </div>
      </section>
    </main>
  );
}
