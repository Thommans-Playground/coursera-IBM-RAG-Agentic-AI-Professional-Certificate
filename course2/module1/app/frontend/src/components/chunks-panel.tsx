"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Slider } from "@/components/ui/slider";
import { getJson, postJson, type Chunk, type IndexSettings } from "@/lib/api";

type Response = { settings: IndexSettings; chunks: Chunk[] };

export function ChunksPanel() {
  const [settings, setSettings] = useState<IndexSettings>({ splitter: "character", chunk_size: 1000, chunk_overlap: 0 });
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    getJson<Response>("/api/chunks")
      .then((d) => {
        setSettings(d.settings);
        setChunks(d.chunks);
        setStatus("");
      })
      .catch(() => setStatus("Cannot reach the backend. Is uvicorn running on port 8000?"));
  }, []);

  async function rebuild() {
    setStatus("Splitting and embedding...");
    try {
      const d = await postJson<Response>("/api/index", settings);
      setChunks(d.chunks);
      setStatus("");
    } catch (e) {
      setStatus((e as Error).message);
    }
  }

  const longest = Math.max(1, ...chunks.map((c) => c.length));

  return (
    <div className="grid gap-6 md:grid-cols-[18rem_1fr]">
      <div className="space-y-5">
        <div className="space-y-2">
          <Label>Splitter</Label>
          <RadioGroup
            value={settings.splitter}
            onValueChange={(v) => setSettings({ ...settings, splitter: v as IndexSettings["splitter"] })}
          >
            <div className="flex items-center gap-2">
              <RadioGroupItem value="character" id="character" />
              <Label htmlFor="character">Character (the lab)</Label>
            </div>
            <div className="flex items-center gap-2">
              <RadioGroupItem value="recursive" id="recursive" />
              <Label htmlFor="recursive">Recursive (better)</Label>
            </div>
          </RadioGroup>
        </div>
        <div className="space-y-2">
          <Label>chunk_size = {settings.chunk_size}</Label>
          <Slider
            min={100}
            max={3000}
            step={100}
            value={[settings.chunk_size]}
            onValueChange={(v) => setSettings({ ...settings, chunk_size: Array.isArray(v) ? v[0] : v })}
          />
        </div>
        <div className="space-y-2">
          <Label>chunk_overlap = {settings.chunk_overlap}</Label>
          <Slider
            min={0}
            max={500}
            step={50}
            value={[settings.chunk_overlap]}
            onValueChange={(v) => setSettings({ ...settings, chunk_overlap: Array.isArray(v) ? v[0] : v })}
          />
        </div>
        <Button onClick={rebuild}>Rebuild index</Button>
        {status && <p className="text-sm text-muted-foreground">{status}</p>}
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">{chunks.length} chunks. Bar length = characters.</p>
        {chunks.map((c) => (
          <div key={c.id} className="space-y-1 rounded border p-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>#{c.id}</span>
              <span>{c.length} chars</span>
              {c.length < 60 && <Badge variant="destructive">tiny, probably a lone heading</Badge>}
            </div>
            <div className="h-1.5 rounded bg-muted">
              <div className="h-1.5 rounded bg-primary" style={{ width: `${(c.length / longest) * 100}%` }} />
            </div>
            <p className="line-clamp-2 text-sm">{c.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
