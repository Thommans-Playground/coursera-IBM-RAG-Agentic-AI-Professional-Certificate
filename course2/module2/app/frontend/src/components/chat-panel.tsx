"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { postJson, type Settings, type Source, type Turn } from "@/lib/api";

type Message = Turn & { sources?: Source[] };

export function ChatPanel({ settings }: { settings: Settings }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    const q = question.trim();
    if (!q || busy) return;
    setBusy(true);
    setQuestion("");
    // The server keeps no chat state, so we send the history with every question.
    const history: Turn[] = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: q }]);
    try {
      const data = await postJson<{ answer: string; sources: Source[] }>("/api/ask", {
        question: q,
        history,
        k: settings.k,
        model: settings.model,
        style: settings.style,
      });
      setMessages((m) => [...m, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${(e as Error).message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {messages.map((m, i) => (
          <Card key={i} className={m.role === "user" ? "bg-muted" : ""}>
            <CardContent className="space-y-2 text-sm">
              <p className="font-medium">{m.role === "user" ? "You" : "Bot"}</p>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {settings.showSources && m.sources && (
                <details>
                  <summary className="cursor-pointer text-muted-foreground">Sources ({m.sources.length})</summary>
                  <ul className="mt-2 space-y-2">
                    {m.sources.map((s, j) => (
                      <li key={j} className="rounded border p-2">
                        <span className="text-xs text-muted-foreground">
                          {s.source} at character {s.start_index}
                        </span>
                        <p className="mt-1 line-clamp-4">{s.text}</p>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      <Textarea
        value={question}
        placeholder="Ask about your notes..."
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
          }
        }}
      />
      <div className="flex gap-2">
        <Button onClick={send} disabled={busy}>
          {busy ? "Thinking..." : "Ask"}
        </Button>
        <Button variant="outline" onClick={() => setMessages([])}>
          Clear chat
        </Button>
      </div>
    </div>
  );
}
