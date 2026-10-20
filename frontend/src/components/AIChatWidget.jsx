import { useEffect, useRef, useState } from "react";
import "./AIChatWidget.css";

const RENDER_URL = "https://clashofcode-4cz0.onrender.com";
const LOCAL_URL = "http://localhost:8000";

const configuredURL = import.meta.env.VITE_API_BASE_URL;
const isLocalRuntime =
  typeof window !== "undefined" &&
  ["localhost", "127.0.0.1", "0.0.0.0"].includes(window.location.hostname);
const apiURLPromise = Promise.resolve(
  configuredURL || (isLocalRuntime ? LOCAL_URL : RENDER_URL)
);

export default function AIChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [messages, loading]);

  async function sendMessage(e) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const apiURL = await apiURLPromise; // instant after first resolution
      const res = await fetch(`${apiURL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Server error ${res.status}`);
      }

      const data = await res.json();
      const reply = data?.reply ?? "(no reply)";
      setMessages((m) => [...m, { role: "ai", text: reply }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "ai", text: `Error contacting AI service: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className={`ai-chat-widget ${open ? "ai-chat--open" : ""}`}>
      <div className="ai-chat-toggle-wrap">
        {open && (
          <div className="ai-chat-panel" role="dialog" aria-label="AI Assistant">
            <div className="ai-chat-header">
              <div className="ai-chat-title">AI Assistant</div>
              <button className="ai-chat-close" onClick={() => setOpen(false)} aria-label="Close">×</button>
            </div>

            <div className="ai-chat-messages" ref={containerRef}>
              {messages.length === 0 && (
                <div className="ai-chat-empty">Say hello — the assistant is ready.</div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`ai-chat-message ai-chat-message--${m.role}`}>
                  <div className="ai-chat-bubble">{m.text}</div>
                </div>
              ))}
              {loading && (
                <div className="ai-chat-message ai-chat-message--ai">
                  <div className="ai-chat-bubble">…</div>
                </div>
              )}
            </div>

            <form className="ai-chat-form" onSubmit={sendMessage}>
              <input
                className="ai-chat-input"
                placeholder="Ask the assistant..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <button type="submit" className="ai-chat-send" disabled={loading || !input.trim()}>
                Send
              </button>
            </form>
          </div>
        )}

        <button
          className="ai-chat-toggle"
          aria-label={open ? "Close chat" : "Open chat"}
          onClick={() => setOpen((o) => !o)}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M12 2v6" />
            <path d="M12 22v-6" />
            <path d="M2 12h6" />
            <path d="M22 12h-6" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </button>
      </div>
    </div>
  );
}