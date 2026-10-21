"use client";

import { Button } from "@/components/ui/button";
import type { Conversation } from "@/lib/api";

type Props = {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
};

export function Sidebar({ conversations, activeId, onSelect, onNew, onDelete }: Props) {
  return (
    <aside className="flex w-64 shrink-0 flex-col gap-2 border-r p-3">
      <Button onClick={onNew}>New chat</Button>
      <ul className="space-y-1 overflow-y-auto">
        {conversations.map((c) => (
          <li key={c.id} className="flex items-center gap-1">
            <Button
              variant={c.id === activeId ? "secondary" : "ghost"}
              className="min-w-0 flex-1 justify-start"
              onClick={() => onSelect(c.id)}
            >
              <span className="truncate">{c.title}</span>
            </Button>
            <Button variant="ghost" size="sm" aria-label={`Delete ${c.title}`} onClick={() => onDelete(c.id)}>
              x
            </Button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
