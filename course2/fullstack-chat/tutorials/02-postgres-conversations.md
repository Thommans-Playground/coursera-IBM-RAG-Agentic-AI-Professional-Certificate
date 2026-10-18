# Tutorial 2: Saved Conversations With Postgres

**What you build.** Your streaming chat from [part 1](01-hello-world-to-streaming-chat.md) now **remembers**. Every conversation and message is saved in **PostgreSQL**. A sidebar lists your chats, the model sees the earlier messages, and a refresh loses nothing.

Everything here is real: a real Postgres database in Docker, the real OpenAI API. No fakes.

This is part 2 of 5:

| Part | Adds |
|---|---|
| [1](01-hello-world-to-streaming-chat.md) | Streaming chat |
| **2** | **Postgres: saved conversations** |
| [3](03-pgvector-owasp-knowledge-base.md) | pgvector: an OWASP Top 10 knowledge base and RAG |
| [4](04-redis-and-celery.md) | Redis and Celery: background loading and rate limiting |
| [5](05-docker-compose.md) | **Docker**: one command runs it all |

## The path

```mermaid
flowchart LR
    S1["1 Why Postgres, start it"] --> S2["2 Learn the SQL we need"]
    S2 --> S3["3 Schema and connection"]
    S3 --> S4["4 Store: all SQL in one file"]
    S4 --> S5["5 Routes and history"]
    S5 --> S6["6 Try with curl"]
    S6 --> S7["7 Sidebar and chat page"]
```

---

## Step 1: Why Postgres, and starting it

### The problem

Part 1 forgets everything on refresh, and the model only ever sees your latest message. A chat needs **storage** outside any single request.

### The fix: PostgreSQL

**PostgreSQL** is a relational database: data lives in **tables** of rows and columns, and tables can point to each other. It is durable (data survives restarts), and it will also store our **vectors** in part 3 with the `pgvector` extension. So we use one database for both chats and knowledge.

```mermaid
flowchart LR
    P["Page"] --> A["FastAPI"] --> D[("Postgres")]
    A --> M["OpenAI"]
```

### Type this

In `my-chat/` create `docker-compose.yml`. We use the image `pgvector/pgvector`, which is Postgres with the vector extension already installed, so we will not change it later:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17   # Postgres with the pgvector extension installed
    environment:
      POSTGRES_USER: chat
      POSTGRES_PASSWORD: chat
      POSTGRES_DB: chat
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data   # keeps your data when the container restarts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chat"]
      interval: 3s
      retries: 20

volumes:
  pgdata:
```

Start it:

```bash
cd course2/fullstack-chat/my-chat
docker compose up -d
docker compose exec postgres psql -U chat chat -c "select version();"
```

**What you should see:** a line starting with `PostgreSQL 17`.

> The password `chat` is fine on your laptop. A real deployment uses a secret and does not publish port 5432 to the world.

### Check yourself

What does the `volumes` line protect you from?

<details>
<summary>Answer</summary>

Losing your data when the container is removed or recreated. The named volume `pgdata` lives outside the container.
</details>

---

## Step 2: The SQL we need

### The idea

Open a SQL prompt:

```bash
docker compose exec postgres psql -U chat chat
```

Try these. They are the same shapes our app will run.

```sql
CREATE TABLE demo_chats (id text PRIMARY KEY, title text);
CREATE TABLE demo_msgs (id bigserial PRIMARY KEY, chat_id text REFERENCES demo_chats(id) ON DELETE CASCADE, body text);

INSERT INTO demo_chats VALUES ('a1', 'Trip plan');
INSERT INTO demo_msgs (chat_id, body) VALUES ('a1', 'hello'), ('a1', 'hi there');

SELECT * FROM demo_msgs WHERE chat_id = 'a1' ORDER BY id;
DELETE FROM demo_chats WHERE id = 'a1';
SELECT count(*) FROM demo_msgs;
```

The last count is `0`. `ON DELETE CASCADE` deleted the messages with their chat. Clean up with `DROP TABLE demo_msgs; DROP TABLE demo_chats;` and leave with `\q`.

| Word | Meaning |
|---|---|
| **table** | A grid of rows and columns, like a spreadsheet with rules. |
| **primary key** | The column that identifies a row. |
| **foreign key** (`REFERENCES`) | A column that points at a row in another table. |
| **cascade** | Delete the children when the parent goes. |
| `ORDER BY id` | Sort the result. |

```mermaid
flowchart LR
    C["conversations: id, title"] -->|"one to many"| M["messages: conversation_id, role, content"]
```

### Check yourself

Why do messages have a `conversation_id` column?

<details>
<summary>Answer</summary>

It says which conversation each message belongs to. One conversation has many messages.
</details>

---

## Step 3: Schema and connection

### Type this

Create `backend/schema.sql`. Every statement says `IF NOT EXISTS`, so it is safe to run on every start:

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id          text PRIMARY KEY,
    title       text NOT NULL DEFAULT 'New chat',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id               bigserial PRIMARY KEY,
    conversation_id  text NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             text NOT NULL CHECK (role IN ('user', 'assistant')),
    content          text NOT NULL,
    sources          jsonb NOT NULL DEFAULT '[]',
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_conv_idx ON messages (conversation_id, id);
```

`sources` is `jsonb`: Postgres can store JSON and still query it. We will use it for citations in part 3. The index makes "all messages of one conversation, in order" fast.

Create `backend/settings.py`:

```python
# needs: your backend folder (file: settings.py)
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chat:chat@localhost:5432/chat")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # 1536 dimensions, used in part 3
FRONTEND_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
HISTORY_LIMIT = 10  # last N messages sent to the model
```

Create `backend/db.py`. The API uses an **async connection pool**: a few open connections that requests borrow and return, because opening a connection for every request is slow.

```python
# needs: your backend folder (file: db.py)
"""Postgres connections. The API uses an async pool."""
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

import settings

SCHEMA = Path(__file__).with_name("schema.sql")


def init_schema() -> None:
    # Safe to run on every start: every statement says IF NOT EXISTS.
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        conn.execute(SCHEMA.read_text())


def make_pool() -> AsyncConnectionPool:
    return AsyncConnectionPool(
        settings.DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={"row_factory": dict_row, "autocommit": True},
    )
```

`dict_row` makes each row a Python dictionary (`row["title"]`) instead of a tuple. `autocommit` saves each statement at once.

`backend/deps.py` hands the pool to routes:

```python
# needs: your backend folder (file: deps.py)
from fastapi import Request
from psycopg_pool import AsyncConnectionPool


def get_pool(request: Request) -> AsyncConnectionPool:
    return request.app.state.pool
```

---

## Step 4: The store, all SQL in one file

### The idea

All SQL goes into `store.py`. The rest of the app says "create a conversation" and never writes SQL.

**Always pass values as parameters** (`%s` plus a tuple), never by gluing strings together. That blocks **SQL injection**, the same risk you will study in the OWASP Top 10 (A05:2025) in part 3.

### Type this

```python
# needs: your backend folder (file: store.py)
"""Every SQL statement lives here. Other files ask in plain words."""
import uuid

from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

DEFAULT_TITLE = "New chat"


# Small helpers. A pool hands out a connection for the length of one `with` block.
async def execute(pool: AsyncConnectionPool, sql: str, params=None) -> None:
    async with pool.connection() as conn:
        await conn.execute(sql, params)


async def one(pool: AsyncConnectionPool, sql: str, params=None) -> dict | None:
    async with pool.connection() as conn:
        return await (await conn.execute(sql, params)).fetchone()


async def many(pool: AsyncConnectionPool, sql: str, params=None) -> list[dict]:
    async with pool.connection() as conn:
        return await (await conn.execute(sql, params)).fetchall()
```

Then the conversation functions. Add below:

```python
# needs: your backend folder (file: store.py, append)
async def create_conversation(pool: AsyncConnectionPool) -> dict:
    cid = uuid.uuid4().hex[:8]
    await execute(pool, "INSERT INTO conversations (id) VALUES (%s)", (cid,))
    return {"id": cid, "title": DEFAULT_TITLE}


async def conversation_exists(pool: AsyncConnectionPool, cid: str) -> bool:
    return await one(pool, "SELECT 1 FROM conversations WHERE id = %s", (cid,)) is not None


async def list_conversations(pool: AsyncConnectionPool) -> list[dict]:
    return await many(pool, "SELECT id, title FROM conversations ORDER BY created_at DESC")


async def delete_conversation(pool: AsyncConnectionPool, cid: str) -> None:
    await execute(pool, "DELETE FROM conversations WHERE id = %s", (cid,))  # messages go too (ON DELETE CASCADE)
```

And messages:

```python
# needs: your backend folder (file: store.py, append)
async def add_message(pool: AsyncConnectionPool, cid: str, role: str, content: str, sources: list | None = None) -> None:
    await execute(
        pool,
        "INSERT INTO messages (conversation_id, role, content, sources) VALUES (%s, %s, %s, %s)",
        (cid, role, content, Jsonb(sources or [])),
    )
    if role == "user":  # the first message names the chat
        await execute(
            pool,
            "UPDATE conversations SET title = %s WHERE id = %s AND title = %s",
            (content[:40], cid, DEFAULT_TITLE),
        )


async def get_messages(pool: AsyncConnectionPool, cid: str, limit: int | None = None) -> list[dict]:
    # Newest N, then put them back in time order.
    return await many(
        pool,
        "SELECT role, content, sources FROM ("
        "  SELECT id, role, content, sources FROM messages WHERE conversation_id = %s ORDER BY id DESC LIMIT %s"
        ") recent ORDER BY id",
        (cid, limit),
    )
```

(`LIMIT NULL` means "no limit" in Postgres, so passing `None` gets everything.)

### Why it works

`UPDATE ... WHERE title = 'New chat'` only renames a chat that still has the default title, so the **first** message names it and later ones do not.

### Check yourself

Why do we sort newest-first in the inner query and then re-sort?

<details>
<summary>Answer</summary>

To take the **last N** rows we need newest first plus `LIMIT`. Then the model needs them in time order, so the outer query sorts again by `id`.
</details>

---

## Step 5: Routes, history and the chat

### The problem

The chat endpoint needs a conversation id, must save messages, and must send the **history** to the model each time. The model has no memory of its own. **Memory is us sending earlier messages again.**

```mermaid
sequenceDiagram
    participant P as Page
    participant A as FastAPI
    participant D as Postgres
    participant M as OpenAI
    P->>A: POST chat for conversation c1
    A->>D: read the last 10 messages
    A->>D: save the user message
    A->>M: history and question, stream
    M-->>A: tokens
    A-->>P: tokens
    A->>D: save the full answer
```

### Type this

`backend/llm.py`:

```python
# needs: your backend folder (file: llm.py)
"""Prompts and the model calls."""
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import settings

PLAIN = "You are a helpful assistant. Keep answers short."


def get_llm(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(model=settings.CHAT_MODEL, **kwargs)


def to_messages(history: list[dict]):
    return [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]


async def stream_answer(history: list[dict], question: str) -> AsyncIterator[str]:
    messages = [SystemMessage(PLAIN), *to_messages(history), HumanMessage(question)]
    async for chunk in get_llm(temperature=0.3, max_tokens=500).astream(messages):
        if chunk.content:
            yield chunk.content
```

`backend/conversations.py`:

```python
# needs: your backend folder (file: conversations.py)
from fastapi import APIRouter, Depends, HTTPException
from psycopg_pool import AsyncConnectionPool

import store
from deps import get_pool

router = APIRouter(prefix="/api/conversations")


@router.get("")
async def list_all(pool: AsyncConnectionPool = Depends(get_pool)):
    return await store.list_conversations(pool)


@router.post("")
async def create(pool: AsyncConnectionPool = Depends(get_pool)):
    return await store.create_conversation(pool)


@router.get("/{cid}/messages")
async def messages(cid: str, pool: AsyncConnectionPool = Depends(get_pool)):
    if not await store.conversation_exists(pool, cid):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await store.get_messages(pool, cid)


@router.delete("/{cid}")
async def delete(cid: str, pool: AsyncConnectionPool = Depends(get_pool)):
    await store.delete_conversation(pool, cid)
    return {"deleted": cid}
```

`backend/chat.py`. Note the order: check, read history, save, then stream:

```python
# needs: your backend folder (file: chat.py)
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field

import llm
import settings
import store
from deps import get_pool

router = APIRouter(prefix="/api/conversations")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=4, ge=1, le=10)  # used in part 3


def sse(event: dict) -> str:
    # One server-sent event: a line starting with "data:" and a blank line after it.
    return f"data: {json.dumps(event)}\n\n"


@router.post("/{cid}/chat")
async def chat(cid: str, body: ChatIn, pool: AsyncConnectionPool = Depends(get_pool)):
    if not await store.conversation_exists(pool, cid):
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = await store.get_messages(pool, cid, limit=settings.HISTORY_LIMIT)
    await store.add_message(pool, cid, "user", body.message)

    async def events():
        parts: list[str] = []
        try:
            async for token in llm.stream_answer(history, body.message):
                parts.append(token)
                yield sse({"type": "token", "text": token})
        except Exception as e:  # tell the page, instead of cutting the stream
            yield sse({"type": "error", "message": str(e)[:200]})
            return
        await store.add_message(pool, cid, "assistant", "".join(parts))
        yield sse({"type": "done"})

    return StreamingResponse(events(), media_type="text/event-stream")
```

We read the history **before** saving the new message, so the question is not sent twice.

`backend/main.py`. A **lifespan** function runs when the server starts and stops: it creates the tables, opens the pool, and closes it at the end.

```python
# needs: your backend folder (file: main.py)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import chat
import conversations
import db
import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    app.state.pool = db.make_pool()
    await app.state.pool.open()
    yield
    await app.state.pool.close()


app = FastAPI(title="Chat", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}
```

### Check yourself

Why does `chat` check that the conversation exists before doing anything else?

<details>
<summary>Answer</summary>

Saving a message for a missing conversation would break the foreign key. Checking first gives a clean `404` instead of a database error.
</details>

---

## Step 6: Try it with curl

Postgres must be running. Start the API:

```bash
cd course2/fullstack-chat/my-chat/backend
uv run uvicorn main:app --reload --port 8000
```

```bash
curl -s -X POST localhost:8000/api/conversations
# use the id you got in place of c1
curl -N -X POST localhost:8000/api/conversations/c1/chat -H "Content-Type: application/json" -d '{"message":"My name is Sam."}'
curl -N -X POST localhost:8000/api/conversations/c1/chat -H "Content-Type: application/json" -d '{"message":"What is my name?"}'
curl -s localhost:8000/api/conversations/c1/messages
```

**What you should see:** the second answer says "Sam", and the last call lists four messages. Now look at the database itself:

```bash
docker compose exec postgres psql -U chat chat -c "select id, role, left(content, 40) as content from messages order by id;"
```

Stop uvicorn, start it again, and fetch the messages again. They are still there. That is the point of Postgres.

---

## Step 7: The sidebar and the chat page

### The idea

The page needs a list of conversations, a "New chat" button and a chat area for the selected one.

```mermaid
flowchart LR
    S["Sidebar: list, new, delete"] --> H["Home page: active id"]
    H --> C["ChatView for the active id"]
    C --> API["api.ts"]
    S --> API
```

### Type this

The API helper. It includes functions for later parts, so you will not edit it again:

```ts
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
```

The sidebar, `src/components/sidebar.tsx`:

```tsx
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
```

The chat view, `src/components/chat-view.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getMessages, streamChat, type Message } from "@/lib/api";

type Props = { cid: string; onActivity: () => void };

export function ChatView({ cid, onActivity }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    getMessages(cid)
      .then((m) => alive && setMessages(m))
      .catch((e) => alive && setError((e as Error).message));
    return () => {
      alive = false;
    };
  }, [cid]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(override?: string) {
    const text = (override ?? input).trim();
    if (!text || busy) return;
    setBusy(true);
    setError("");
    setInput("");
    // Add the user's message and an empty bot message that we fill as tokens arrive.
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    const patchLast = (fn: (m: Message) => Message) =>
      setMessages((all) => all.map((m, i) => (i === all.length - 1 ? fn(m) : m)));
    try {
      for await (const event of streamChat(cid, text)) {
        if (event.type === "token") patchLast((m) => ({ ...m, content: m.content + event.text }));
        if (event.type === "error") setError(event.message);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      onActivity(); // the first message gives the chat its title
    }
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "ml-auto max-w-[80%] rounded-lg bg-muted p-3" : "max-w-[80%] p-3"}>
            <p className="whitespace-pre-wrap text-sm">{m.content || (busy ? "..." : "")}</p>
          </div>
        ))}
        <div ref={bottom} />
      </div>
      {error && <p className="px-4 text-sm text-destructive">{error}</p>}
      <div className="flex gap-2 border-t p-3">
        <Textarea
          value={input}
          placeholder="Message..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <Button onClick={() => send()} disabled={busy}>
          Send
        </Button>
      </div>
    </div>
  );
}
```

The page, `src/app/page.tsx`:

```tsx
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
```

Run `npm run dev` (with uvicorn and Postgres running).

**What you should see:** "New chat" makes an entry. Type a message and watch it stream. The sidebar title changes to your first words. Refresh: your chats are still there. Make a second chat and switch between them.

### Why it works

- `ChatView key={activeId}` builds a **new** ChatView for each conversation, so old messages never leak into another chat.
- Messages load from the backend whenever `cid` changes.
- `onActivity` refreshes the sidebar after each answer, which picks up the new title.
- The `alive` flag stops a slow answer for an old conversation from overwriting the new one.

### Try it

1. Delete a chat with `x`. Then `select count(*) from messages;` in psql. Did its messages go too?
2. Open a chat in two browser tabs and send messages from both. What does each tab show after a refresh?

---

## Common mistakes

| Mistake | What you see | Fix |
|---|---|---|
| Postgres not running | `connection refused` on port 5432 when uvicorn starts | `docker compose up -d`, wait for the health check. |
| Port 5432 already used | `docker compose up` fails | Stop the other Postgres or change the left side of `"5432:5432"` and your `DATABASE_URL`. |
| Built SQL by gluing strings | Works, until someone sends `'; DROP TABLE ...` | Always `%s` parameters. |
| Forgot `autocommit` | Rows missing after the request | Keep `autocommit: True` in the pool `kwargs`. |
| Sent the new message in the history too | The model sees the question twice | Read history before `add_message`. |
| Messages from another chat appear | Old text after switching | `key={activeId}` on `ChatView`. |
| `tuple indices must be integers` | Error in `store.py` | You lost `row_factory: dict_row`. |
| Changed `schema.sql` but nothing changed | Old columns | `IF NOT EXISTS` skips tables that exist. Alter them with SQL or recreate the volume. |

## Practice

No answers shown. Ask me for a hint.

1. **Rename a chat.** Add `PATCH /api/conversations/{id}` that changes the title. Which SQL statement?
2. **Message count.** Show "(6 messages)" next to each chat in the sidebar. Use one query with `GROUP BY`.
3. **Stop at 4000 characters.** Send the last 10 messages, but stop adding older ones once the total passes 4000 characters. Where do you do it, SQL or Python?
4. **A second table.** Add a `feedback` table (thumbs up or down per message). What is its foreign key?
5. **Look inside.** In psql, find the longest message in your database.
6. **Explain it.** In five sentences, explain how the model "remembers" when it has no memory.

## Cheat sheet

| Need | SQL or code | Where |
|---|---|---|
| Create a chat | `INSERT INTO conversations` | `create_conversation` |
| Newest chats first | `ORDER BY created_at DESC` | `list_conversations` |
| Last N messages in order | subquery with `LIMIT`, then `ORDER BY id` | `get_messages` |
| Remove a chat and its messages | `DELETE` plus `ON DELETE CASCADE` | `delete_conversation` |
| Borrow a connection | `async with pool.connection()` | `store.py` helpers |
| Create tables at start | `schema.sql` plus `lifespan` | `db.init_schema` |

Next: [Part 3: pgvector and an OWASP Top 10 knowledge base](03-pgvector-owasp-knowledge-base.md).
