"use client";

import { useEffect, useState } from "react";
import { getCalendarEvents, getSessionStatus } from "@/lib/api";
import type { TCalendarEvent } from "@/lib/api";

type LoadState = "loading" | "signed-out" | "error" | "ready";

function formatEventStart(event: TCalendarEvent): string {
  if (event.start.dateTime) {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(event.start.dateTime));
  }

  if (event.start.date) {
    return `All day · ${new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
    }).format(new Date(`${event.start.date}T00:00:00`))}`;
  }

  return "No date";
}

export default function CalendarEvents() {
  const [events, setEvents] = useState<TCalendarEvent[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState("Couldn't load events.");

  useEffect(() => {
    async function loadEvents() {
      try {
        const session = await getSessionStatus();
        if (!session.authenticated) {
          setState("signed-out");
          return;
        }

        const timeMin = new Date();
        const timeMax = new Date(timeMin);
        timeMax.setDate(timeMax.getDate() + 7);

        const calendarEvents = await getCalendarEvents(
          timeMin.toISOString(),
          timeMax.toISOString(),
        );

        setEvents(calendarEvents);
        setState("ready");
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "Couldn't load events.",
        );
        setState("error");
      }
    }

    void loadEvents();
  }, []);

  if (state === "loading") return <p>Loading events…</p>;
  if (state === "signed-out") return <p>Connect your Google account to view events.</p>;
  if (state === "error") return <p>{errorMessage}</p>;
  if (events.length === 0) return <p>No events in the next 7 days.</p>;

  return (
    <section aria-labelledby="calendar-events-heading" className="mt-2">
      <h2 id="calendar-events-heading">Upcoming events</h2>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            <strong>{event.summary || "No title"}</strong>&nbsp;
            <time>{formatEventStart(event)}</time>
          </li>
        ))}
      </ul>
    </section>
  );
}