// In dev: VITE_API_URL is empty, so calls go to "/api/..." (Vite proxy handles it)
// In prod: VITE_API_URL = "https://university-support-assistant.onrender.com"

const BASE = import.meta.env.VITE_API_URL || "";

export async function sendMessage(sessionId, message) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.status}`);
  return res.json();
}

export async function newSession() {
  const res = await fetch(`${BASE}/api/session/new`, { method: "POST" });
  if (!res.ok) throw new Error(`Session error: ${res.status}`);
  return res.json();
}

export async function clearSession(sessionId) {
  const res = await fetch(`${BASE}/api/session/${sessionId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Clear error: ${res.status}`);
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new Error(`Health error: ${res.status}`);
  return res.json();
}