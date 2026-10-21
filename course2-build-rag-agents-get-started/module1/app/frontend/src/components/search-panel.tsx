"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { postJson, type Hit } from "@/lib/api";

export function SearchPanel() {
  const [question, setQuestion] = useState("Can I smoke in company vehicles?");
  const [k, setK] = useState(4);
  const [hits, setHits] = useState<Hit[]>([]);
  const [error, setError] = useState("");

  async function run() {
    setError("");
    try {
      setHits((await postJson<{ hits: Hit[] }>("/api/search", { question, k })).hits);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        This is retrieval only: no LLM, no answer. You see what the retriever hands to the model.
      </p>
      <Label htmlFor="q">Question</Label>
      <Input id="q" value={question} onChange={(e) => setQuestion(e.target.value)} />
      <div className="max-w-xs space-y-2">
        <Label>k = {k}</Label>
        <Slider min={1} max={10} step={1} value={[k]} onValueChange={(v) => setK(Array.isArray(v) ? v[0] : v)} />
      </div>
      <Button onClick={run}>Search</Button>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <ol className="space-y-2">
        {hits.map((h, i) => (
          <li key={h.id} className="rounded border p-3 text-sm">
            <p className="text-xs text-muted-foreground">
              rank {i + 1}, chunk #{h.id}, cosine score {h.score}
            </p>
            <p className="mt-1 line-clamp-5">{h.text}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
