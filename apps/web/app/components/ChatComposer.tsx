"use client";

import { useState } from "react";
import { chatWithCalendar } from "@/lib/api";

export default function ChatComposer() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSend() {
    const trimmed = message.trim();
    if (!trimmed || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setReply("");

    try {
      const data = await chatWithCalendar(trimmed);
      setReply(data.reply);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong while chatting");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="composer-wrap">
      <div className="composer" aria-label="Assistant message composer">
        <textarea
          aria-label="Message your assistant"
          placeholder="Ask about your calendar..."
          rows={1}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          disabled={loading}
          onKeyDown={(event) => {
            if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
            ){
                event.preventDefault();
                void handleSend();    
            }
        }}
        />
        <button
          className="send-button"
          type="button"
          title="Send message"
          aria-label="Send message"
          onClick={handleSend}
          disabled={loading || !message.trim()}
        >
          <span className="send-icon" aria-hidden="true">
            {loading ? "…" : "↑"}
          </span>
        </button>
      </div>

      {error && (
        <div role="alert" style={{ color: "crimson", marginTop: 8 }}>
          {error}
        </div>
      )}

      {reply && (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            border: "1px solid #d9ded3",
            borderRadius: 8,
            background: "#fff",
            whiteSpace: "pre-wrap",
          }}
        >
          {reply}
        </div>
      )}
      <div className="composer-meta">
        <span>GOOGLE CALENDAR</span>
        <span className="meta-divider" />
        <span>{loading ? "SENDING..." : "CONNECTION REQUIRED"}</span>
      </div>
    </div>
  );
}
