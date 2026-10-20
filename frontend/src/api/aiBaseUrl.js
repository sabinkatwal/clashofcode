// Shared base-URL resolution for the AI-backed endpoints (/chat/, /chat/analyze).
// Tries local dev server first, falls back to Railway. Computed once at
// module load and cached, so every caller (ChatBox, AIAnalysisCard, etc.)
// shares the same resolved URL instead of re-running the health check.

export const RENDER_URL = "https://clashofcode-4cz0.onrender.com";
export const LOCAL_URL = "http://localhost:8000";

const configuredURL = import.meta.env.VITE_API_BASE_URL;
const isLocalRuntime =
  typeof window !== "undefined" &&
  ["localhost", "127.0.0.1", "0.0.0.0"].includes(window.location.hostname);

export const apiURLPromise = Promise.resolve(
  configuredURL || (isLocalRuntime ? LOCAL_URL : RENDER_URL)
);