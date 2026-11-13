import Link from "next/link";
import ApiHealth from "@/app/components/ApiHealth";
import GoogleLoginStatus from "./components/GoogleLoginStatus";
import CalendarEvents from "./components/CalendarEvents";
import ChatComposer from "./components/ChatComposer";

const suggestions = [
  "What's on my calendar next week?",
  "Am I free this Friday after 5 PM?",
  "Add a one-hour workout for Tuesday at 6 PM.",
];

export default function Home() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Calendar Copilot home">
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
            Calendar assistant
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
            CALENDAR COPILOT <span /> YOUR CALENDAR
          </p>
          <h1>
            What&apos;s on
            <br />
            <em>your calendar?</em>
          </h1>
          <p className="welcome-copy">
            Browse upcoming events and plan your next step with the assistant.
          </p>
          <div className="suggestions" aria-label="Example questions">
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
          <CalendarEvents />
        </div>
        <ChatComposer />
      </section>
    </main>
  );
}
