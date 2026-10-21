"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getJson, postFiles } from "@/lib/api";

export function DocumentsPanel() {
  const [sources, setSources] = useState<Record<string, number>>({});
  const [status, setStatus] = useState("");

  useEffect(() => {
    getJson<{ sources: Record<string, number> }>("/api/documents")
      .then((data) => setSources(data.sources))
      .catch(() => setStatus("Cannot reach the backend. Is uvicorn running on port 8000?"));
  }, []);

  async function onPick(files: FileList | null) {
    if (!files || files.length === 0) return;
    setStatus("Indexing...");
    try {
      const data = await postFiles<{ sources: Record<string, number> }>("/api/documents", files);
      setSources(data.sources);
      setStatus("Added.");
    } catch (e) {
      setStatus((e as Error).message);
    }
  }

  return (
    <div className="space-y-3">
      <Label htmlFor="docs">Add .txt or .md files to the knowledge base</Label>
      <Input id="docs" type="file" multiple accept=".txt,.md" onChange={(e) => onPick(e.target.files)} />
      {status && <p className="text-sm text-muted-foreground">{status}</p>}
      <div className="flex flex-wrap gap-2">
        {Object.entries(sources).map(([name, n]) => (
          <Badge key={name} variant="secondary">
            {name}: {n} chunks
          </Badge>
        ))}
      </div>
    </div>
  );
}
