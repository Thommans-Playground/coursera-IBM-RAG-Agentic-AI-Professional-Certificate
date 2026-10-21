export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Chunk = { id: number; length: number; text: string };
export type Hit = { id: number; score: number; text: string };
export type Turn = { role: "user" | "assistant"; content: string };
export type IndexSettings = { splitter: "character" | "recursive"; chunk_size: number; chunk_overlap: number };

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) {
    // FastAPI sends errors as { detail: ... }.
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const getJson = <T,>(path: string) => send<T>(path);

export const postJson = <T,>(path: string, body: unknown) =>
  send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
