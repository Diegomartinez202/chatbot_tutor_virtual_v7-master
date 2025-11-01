// src/services/voice/listVoice.js
export async function listVoice({ page = 1, limit = 20, sender, session_id, q } = {}) {
  const u = new URL("/api/voice/list", location.origin);
  u.searchParams.set("page", String(page));
  u.searchParams.set("limit", String(limit));
  if (sender) u.searchParams.set("sender", sender);
  if (session_id) u.searchParams.set("session_id", session_id);
  if (q) u.searchParams.set("q", q);

  const res = await fetch(u.toString(), { credentials: "include" });
  if (!res.ok) throw new Error(`List voice failed: ${res.status}`);
  return res.json();
}