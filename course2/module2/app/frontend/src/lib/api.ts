export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Turn = { role: "user" | "assistant"; content: string };
export type Source = { source: string; start_index: number; text: string };
export type Settings = { model: string; k: number; style: "concise" | "detailed"; showSources: boolean };

async function send<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) {
    // FastAPI sends errors as { detail: ... }.
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function postJson<T>(path: string, body: unknown) {
  return send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// Do not set Content-Type here: the browser adds the multipart boundary itself.
export function postFiles<T>(path: string, files: FileList) {
  const form = new FormData();
  Array.from(files).forEach((f) => form.append("files", f));
  return send<T>(path, { method: "POST", body: form });
}

export function getJson<T>(path: string) {
  return send<T>(path, {});
}
