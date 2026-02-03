const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function postQuery(query) {
  const res = await fetch(`${API_BASE}/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return res.json();
}
