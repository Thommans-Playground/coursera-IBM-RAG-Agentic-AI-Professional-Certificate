"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { postJson, type Hit, type Turn } from "@/lib/api";

type Message = Turn & { rewritten?: string; hits?: Hit[] };

export function AskPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [k, setK] = useState(4);
  const [strict, setStrict] = useState(true);
  const [memory, setMemory] = useState(true);

  async function send() {
    const q = question.trim();
    if (!q || busy) return;
    setBusy(true);
    setQuestion("");
    // Memory off means an empty history, which is the lab's "no memory" demo.
    const history = memory ? messages.map(({ role, content }) => ({ role, content })) : [];
    setMessages((m) => [...m, { role: "user", content: q }]);
    try {
      const d = await postJson<{ answer: string; standalone_question: string; hits: Hit[] }>("/api/ask", {
        question: q,
        k,
        strict,
        history,
      });
      const rewritten = d.standalone_question !== q ? d.standalone_question : undefined;
      setMessages((m) => [...m, { role: "assistant", content: d.answer, rewritten, hits: d.hits }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${(e as Error).message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-[1fr_16rem]">
      <div className="space-y-4">
        {messages.map((m, i) => (
          <Card key={i} className={m.role === "user" ? "bg-muted" : ""}>
            <CardContent className="space-y-2 text-sm">
              <p className="font-medium">{m.role === "user" ? "You" : "Bot"}</p>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.rewritten && <p className="text-xs text-muted-foreground">Searched for: {m.rewritten}</p>}
              {m.hits && (
                <details>
                  <summary className="cursor-pointer text-muted-foreground">Chunks used ({m.hits.length})</summary>
                  <ul className="mt-2 space-y-2">
                    {m.hits.map((h) => (
                      <li key={h.id} className="rounded border p-2">
                        <span className="text-xs text-muted-foreground">
                          chunk #{h.id}, score {h.score}
                        </span>
                        <p className="line-clamp-4">{h.text}</p>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </CardContent>
          </Card>
        ))}
        <Textarea
          value={question}
          placeholder="Ask about the Innovatech policies..."
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

      <div className="space-y-5">
        <div className="space-y-2">
          <Label>k = {k}</Label>
          <Slider min={1} max={10} step={1} value={[k]} onValueChange={(v) => setK(Array.isArray(v) ? v[0] : v)} />
        </div>
        <div className="flex items-center gap-2">
          <Checkbox id="strict" checked={strict} onCheckedChange={(c) => setStrict(c === true)} />
          <Label htmlFor="strict">Say &quot;I don&apos;t know&quot; rule</Label>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox id="memory" checked={memory} onCheckedChange={(c) => setMemory(c === true)} />
          <Label htmlFor="memory">Memory</Label>
        </div>
      </div>
    </div>
  );
}
