"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { listDocuments, uploadDocuments, type DocInfo } from "@/lib/api";

export function DocumentsPanel({ cid }: { cid: string }) {
  const [docs, setDocs] = useState<DocInfo[]>([]);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);

  // Poll while any document is still being processed by the worker.
  const pending = docs.some((d) => d.status === "queued" || d.status === "processing");

  useEffect(() => {
    let alive = true;
    listDocuments(cid)
      .then((d) => alive && setDocs(d))
      .catch((e) => alive && setError((e as Error).message));
    return () => {
      alive = false;
    };
  }, [cid, tick]);

  useEffect(() => {
    if (!pending) return;
    const timer = setTimeout(() => setTick((t) => t + 1), 1500);
    return () => clearTimeout(timer);
  }, [pending, tick]);

  async function onPick(files: FileList | null) {
    if (!files || files.length === 0) return;
    setError("");
    try {
      await uploadDocuments(cid, files);
      setTick((t) => t + 1);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-2 border-b p-3">
      <div className="flex items-center gap-3">
        <label htmlFor="docs" className="text-sm font-medium">
          Documents for this chat
        </label>
        <Input id="docs" type="file" multiple accept=".txt,.md" className="max-w-xs" onChange={(e) => onPick(e.target.files)} />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex flex-wrap gap-2">
        {docs.map((d) => (
          <Badge key={d.id} variant={d.status === "failed" ? "destructive" : "secondary"} title={d.error}>
            {d.name}: {d.status}
            {d.status === "ready" ? ` (${d.chunks} chunks)` : ""}
          </Badge>
        ))}
      </div>
    </div>
  );
}
