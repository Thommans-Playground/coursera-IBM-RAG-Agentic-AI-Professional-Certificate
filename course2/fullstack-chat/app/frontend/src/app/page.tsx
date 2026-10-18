"use client";

import { useEffect, useState } from "react";
import { ChatView } from "@/components/chat-view";
import { Sidebar } from "@/components/sidebar";
import {
  createConversation,
  deleteConversation,
  listConversations,
  type Conversation,
} from "@/lib/api";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function refresh() {
    setConversations(await listConversations());
  }

  useEffect(() => {
    listConversations()
      .then((list) => {
        setConversations(list);
        setActiveId((current) => current ?? list[0]?.id ?? null);
      })
      .catch(() => setError("Cannot reach the backend. Is uvicorn running on port 8000?"));
  }, []);

  async function onNew() {
    const c = await createConversation();
    await refresh();
    setActiveId(c.id);
  }

  async function onDelete(id: string) {
    await deleteConversation(id);
    const list = await listConversations();
    setConversations(list);
    if (id === activeId) setActiveId(list[0]?.id ?? null);
  }

  return (
    <div className="flex h-screen">
      <Sidebar conversations={conversations} activeId={activeId} onSelect={setActiveId} onNew={onNew} onDelete={onDelete} />
      {activeId ? (
        <ChatView key={activeId} cid={activeId} onActivity={refresh} />
      ) : (
        <div className="m-auto text-sm text-muted-foreground">{error || "Press New chat to start."}</div>
      )}
    </div>
  );
}
