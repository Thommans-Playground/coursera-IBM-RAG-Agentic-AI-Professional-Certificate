"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listKnowledge, loadKnowledge, type KbDoc } from "@/lib/api";

export function KnowledgePanel() {
  const [docs, setDocs] = useState<KbDoc[]>([]);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);

  // Poll while the worker is still processing any category.
  const pending = docs.some((d) => d.status === "queued" || d.status === "processing");

  useEffect(() => {
    let alive = true;
    listKnowledge()
      .then((d) => alive && setDocs(d))
      .catch(() => alive && setError("Cannot reach the backend. Is uvicorn running on port 8000?"));
    return () => {
      alive = false;
    };
  }, [tick]);

  useEffect(() => {
    if (!pending) return;
    const timer = setTimeout(() => setTick((t) => t + 1), 1500);
    return () => clearTimeout(timer);
  }, [pending, tick]);

  async function load() {
    setError("");
    try {
      await loadKnowledge();
      setTick((t) => t + 1);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const ready = docs.filter((d) => d.status === "ready").length;

  return (
    <div className="space-y-2 border-b p-3">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-medium">
          OWASP Top 10:2025 knowledge base ({ready}/{docs.length || 10} ready)
        </span>
        <Button size="sm" variant="outline" onClick={load} disabled={pending}>
          {docs.length === 0 ? "Load OWASP Top 10" : "Reload"}
        </Button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex flex-wrap gap-2">
        {docs.map((d) => (
          <Badge key={d.id} variant={d.status === "failed" ? "destructive" : "secondary"} title={d.error}>
            {d.key}: {d.status}
          </Badge>
        ))}
      </div>
    </div>
  );
}
