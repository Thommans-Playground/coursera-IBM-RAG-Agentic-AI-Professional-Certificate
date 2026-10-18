export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Conversation = { id: string; title: string };
export type Source = { title: string; url: string; text: string; score: number };
export type Message = { role: "user" | "assistant"; content: string; sources?: Source[] };
export type KbDoc = { id: number; key: string; title: string; status: "queued" | "processing" | "ready" | "failed"; chunks: number; error: string };
export type ChatEvent =
  | { type: "token"; text: string }
  | { type: "sources"; sources: Source[] }
  | { type: "error"; message: string }
  | { type: "done" };

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) {
    // FastAPI sends errors as { detail: ... }.
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const listConversations = () => send<Conversation[]>("/api/conversations");
export const createConversation = () => send<Conversation>("/api/conversations", { method: "POST" });
export const deleteConversation = (id: string) => send(`/api/conversations/${id}`, { method: "DELETE" });
export const getMessages = (id: string) => send<Message[]>(`/api/conversations/${id}/messages`);
export const listKnowledge = () => send<KbDoc[]>("/api/knowledge");
export const loadKnowledge = () => send<{ queued: number }>("/api/knowledge/load", { method: "POST" });

// EventSource only supports GET, so we read the POST response stream ourselves.
export async function* streamChat(id: string, message: string): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API}/api/conversations/${id}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? ""; // the last piece may be half an event, keep it for the next read
    for (const e of events) {
      if (e.startsWith("data: ")) yield JSON.parse(e.slice(6)) as ChatEvent;
    }
  }
}
