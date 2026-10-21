# Tutorial 3: Build the RAG Lab as a Web App (Next.js + FastAPI + Postgres)

**What you build.** The Module 1 lab as a small web app, so you can *see* each stage of RAG instead of reading cell output. It has three tabs:

1. **Chunks**: change the splitter, chunk size and overlap, and see the chunks.
2. **Search**: type a question and see exactly which chunks the retriever returns, with scores. No LLM involved.
3. **Ask**: chat with the Innovatech company policies. Switch the "I don't know" rule and memory on and off.

**The vector store is Postgres.** The lab used an in-memory store that forgets everything when the program stops. Here the chunks and their embeddings live in **PostgreSQL with the pgvector extension**, so the index survives restarts and the search is one SQL query. Redis is not used: nothing in this app needs a queue or counters. (The [full-stack OWASP chat](../../fullstack-chat/README.md) adds Redis and Celery when it does.)

**How this tutorial works.** One app, grown in small steps. Each step starts with a **problem**, then the **fix**. It uses the lab's own file, `companyPolicies.txt`. Everything is real: real Postgres in Docker, the real OpenAI API. The LLM is OpenAI (`gpt-4o-mini`) instead of watsonx, as in [Tutorial 1](01-rag-study-guide-and-lab-adapted.md).

New to FastAPI, `fetch`, CORS or shadcn inputs? Read [module 2, Tutorial 1](../../module2/tutorials/01-gradio-concepts-adapted-to-nextjs.md) first. This tutorial reuses those ideas without re-explaining them. The module 2 [RAG web app](../../module2/tutorials/02-build-the-rag-web-app.md) answers from your own uploaded notes. This one is for **learning how RAG behaves**.

A finished copy is in [../app/](../app/), and you can run it with one command: see its [README](../app/README.md). Build yours in `course2/module1/my-lab/` and compare.

## The path

```mermaid
flowchart LR
    S0["0 Hello world"] --> S1["1 Start Postgres"]
    S1 --> S2["2 Pipeline in cells, now a Lab class"]
    S2 --> S3["3 Cannot see the chunks"]
    S3 --> S4["4 Cannot see what retrieval returns"]
    S4 --> S5["5 Bot makes things up"]
    S5 --> S6["6 Bot forgets"]
    S6 --> S7["7 One command: Docker"]
```

## Before you start

- `OPENAI_API_KEY` in the repo-root `.env`, and Docker running.
- Backend packages (`fastapi`, `uvicorn`, `psycopg`, `pgvector`, `langchain-openai` and friends) are in the root `pyproject.toml`.
- Frontend project, from `course2/module1/my-lab/`:

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
cd frontend
npx shadcn@latest init -d -y
npx shadcn@latest add button card input label slider radio-group checkbox textarea badge tabs -y
```

Real API calls cost a few cents. Embedding the policy file takes a fraction of a cent.

---

## Step 0: Hello world

### The idea

Before any database or AI, prove that the two programs can talk. The backend answers on port 8000. The page, on port 3000, asks it a question with `fetch` and shows the reply.

```mermaid
sequenceDiagram
    participant P as Page, port 3000
    participant A as FastAPI, port 8000
    P->>A: GET /api/hello
    A-->>P: message
```

### Type this

Create `backend/main.py`:

```python
# needs: your backend folder (file: hello_main.py)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# The page and the API run on different ports, so the browser needs permission (CORS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}
```

Run it from `backend/`, inside the repo so `uv` uses the shared environment:

```bash
cd course2/module1/my-lab/backend
uv run uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/api/hello. You should see `{"message":"Hello from FastAPI"}`. Also open http://localhost:8000/docs for a free test page.

Now the page. Replace `frontend/src/app/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/api/hello")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch(() => setMessage("Cannot reach the backend. Is uvicorn running?"));
  }, []);

  return <main className="p-6 text-xl">{message}</main>;
}
```

In a second terminal run `npm run dev` inside `frontend/`, then open http://localhost:3000.

**What you should see:** "Hello from FastAPI". Stop uvicorn and refresh: you see the "Cannot reach" text instead.

### Why it works

`"use client"` marks a component that uses state and effects, so it runs in the browser. `useEffect` with `[]` runs once when the page opens. `CORSMiddleware` is needed because port 3000 and port 8000 are different origins, and browsers block the call unless the API allows it.

### Check yourself

What happens if you remove `CORSMiddleware`? (Try it and read the browser console.)

---

## Step 1: Start Postgres

### The idea

**PostgreSQL** is a database that stores data in tables. **pgvector** is an extension that adds a `vector(1536)` column type and operators to compare vectors. We use the image `pgvector/pgvector`, which is Postgres with the extension already installed.

```mermaid
flowchart LR
    A["FastAPI"] --> D[("Postgres + pgvector: lab_chunks")]
    A --> O["OpenAI embeddings and chat"]
```

### Type this

In `my-lab/` create `docker-compose.yml`:

```yaml
name: rag-lab   # a fixed project name, so volumes do not clash with the other apps in this repo

services:
  postgres:
    image: pgvector/pgvector:pg17   # Postgres with the pgvector extension installed
    environment:
      POSTGRES_USER: lab
      POSTGRES_PASSWORD: lab
      POSTGRES_DB: lab
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data   # keeps the index when the container restarts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lab"]
      interval: 3s
      retries: 20

volumes:
  pgdata:
```

```bash
cd course2/module1/my-lab
docker compose up -d
docker compose exec postgres psql -U lab lab -c "select version();"
```

**What you should see:** a line starting with `PostgreSQL 17`.

> The password `lab` is for your laptop only. Port 5432 clashes with any other Postgres you run, including the OWASP chat app's. Stop the other one first.

---

## Step 2: The pipeline is stuck in notebook cells

### The problem

In the lab the pipeline is a row of cells: download, load, split, embed, store. A web server cannot run cells. We need one object that can **build the index** (with chosen settings) and **answer questions**, and a **place to keep the vectors**.

### The fix: a `Lab` class on top of two tables

```mermaid
flowchart LR
    W["main.py: web layer"] --> L["Lab: lab.py"]
    L --> D["Download file"]
    L --> I["build: split, embed, store in Postgres"]
    L --> Q["search: SQL"]
```

### Type this

Create `backend/schema.sql`. Every statement says `IF NOT EXISTS`, so it is safe to run on every start:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- The settings the current index was built with. At most one row.
CREATE TABLE IF NOT EXISTS lab_settings (
    id             int PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    splitter       text NOT NULL,
    chunk_size     int NOT NULL,
    chunk_overlap  int NOT NULL
);

-- One row per chunk. 1536 is the size of text-embedding-3-small vectors.
CREATE TABLE IF NOT EXISTS lab_chunks (
    id         int PRIMARY KEY,
    content    text NOT NULL,
    embedding  vector(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS lab_chunks_embedding_idx ON lab_chunks USING hnsw (embedding vector_cosine_ops);
```

`CHECK (id = 1)` allows only one settings row. The **HNSW index** makes nearest-neighbour search fast on many rows.

Create `backend/db.py`. A **connection pool** keeps a few connections open for requests to borrow:

```python
# needs: your backend folder (file: db.py)
"""Postgres connections. The lab's endpoints are plain `def`, so a normal (sync) pool is enough."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lab:lab@localhost:5432/lab")
SCHEMA = Path(__file__).with_name("schema.sql")


def init_schema() -> None:
    # Safe to run on every start: every statement says IF NOT EXISTS.
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute(SCHEMA.read_text())


def make_pool() -> ConnectionPool:
    return ConnectionPool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        configure=register_vector,  # lets us pass numpy arrays as vectors
        kwargs={"row_factory": dict_row, "autocommit": True},
    )
```

`dict_row` returns each row as a dictionary (`row["id"]`). `register_vector` teaches the driver the `vector` type.

Create `backend/lab.py`. First the imports and the file download (this replaces the lab's `wget`):

```python
# needs: your backend folder (file: lab.py)
"""The lab's RAG pipeline as an object: load, split, embed, store, retrieve."""
import os
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from psycopg_pool import ConnectionPool

load_dotenv()

POLICY_URL = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/6JDbUb_L3egv_eOkouY71A.txt"
# DATA_DIR lets a container keep the downloaded file on a volume.
POLICY_FILE = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent / "data")) / "companyPolicies.txt"


def load_policies() -> str:
    # Downloaded once, like the lab's wget step.
    if not POLICY_FILE.exists():
        POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(POLICY_URL, POLICY_FILE)
    return POLICY_FILE.read_text()
```

Then the class below it, with the **indexing** side and a way to read the index back:

```python
# needs: your backend folder (file: lab.py, append)
class Lab:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text = load_policies()

    def is_built(self) -> bool:
        with self.pool.connection() as conn:
            return conn.execute("SELECT 1 FROM lab_chunks LIMIT 1").fetchone() is not None

    def build(self, splitter: str, chunk_size: int, chunk_overlap: int) -> None:
        cls = CharacterTextSplitter if splitter == "character" else RecursiveCharacterTextSplitter
        chunks = cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap).split_documents(
            [Document(page_content=self.text, metadata={"source": POLICY_FILE.name})]
        )
        texts = [c.page_content for c in chunks]
        vectors = self.embeddings.embed_documents(texts)
        with self.pool.connection() as conn, conn.transaction():  # all or nothing, so a failure keeps the old index
            conn.execute("DELETE FROM lab_chunks")  # replace the whole index, so old chunks do not linger
            for i, (text, vec) in enumerate(zip(texts, vectors)):
                conn.execute("INSERT INTO lab_chunks (id, content, embedding) VALUES (%s, %s, %s)", (i, text, np.array(vec)))
            conn.execute(
                "INSERT INTO lab_settings (id, splitter, chunk_size, chunk_overlap) VALUES (1, %s, %s, %s) "
                "ON CONFLICT (id) DO UPDATE SET splitter = excluded.splitter, "
                "chunk_size = excluded.chunk_size, chunk_overlap = excluded.chunk_overlap",
                (splitter, chunk_size, chunk_overlap),
            )

    def state(self) -> dict:
        with self.pool.connection() as conn:
            settings = conn.execute("SELECT splitter, chunk_size, chunk_overlap FROM lab_settings").fetchone()
            rows = conn.execute("SELECT id, length(content) AS length, content AS text FROM lab_chunks ORDER BY id").fetchall()
        return {"settings": settings, "chunks": rows}
```

Try it (this calls the real embedding API once):

```python
# needs: your backend folder (run it from there, with Postgres running)
import db
from lab import Lab

db.init_schema()
pool = db.make_pool()
pool.open()
lab = Lab(pool)
lab.build("character", 1000, 0)
print(len(lab.state()["chunks"]))
pool.close()
```

**What you should see:** `16`, the lab's number. Check the database itself:

```bash
docker compose exec postgres psql -U lab lab -c "select id, length(content), vector_dims(embedding) from lab_chunks order by id limit 4;"
```

You see the chunk lengths and `1536` dimensions.

### Why it works

`build` is the lab's indexing phase: split, embed, store. It runs inside a **transaction** (`conn.transaction()`): the old index is deleted and the new one inserted as one unit. If the embedding call had failed halfway, the old index would still be there. Because the data is in Postgres, **restarting the server does not lose the index**.

### Try it

Run the snippet again. Does the count stay `16`? (It deletes the old rows first.) Then stop and start the container: `docker compose restart postgres`. Is the data still there?

---

## Step 3: I cannot see the chunks

### The problem

The lab prints `16` and moves on. You never see that half of those chunks are lone headings. The effect of `chunk_size` and `overlap` is invisible.

### The fix: an endpoint that returns chunks, and a page that draws them

```mermaid
sequenceDiagram
    participant P as Chunks tab
    participant A as FastAPI
    participant L as Lab
    participant D as Postgres
    P->>A: POST /api/index with splitter, size, overlap
    A->>L: build(...)
    L->>D: replace the chunks and vectors
    A->>L: state()
    L->>D: read settings and chunks
    A-->>P: id, length, text for each chunk
```

### Type this

Replace `backend/main.py` (the hello world version goes away). A **lifespan** function runs at server start and stop: it creates the tables, opens the pool, builds the first index (only if the database is empty) and closes the pool at the end:

```python
# needs: your backend folder (file: main.py)
"""FastAPI app for the RAG lab. One endpoint per pipeline stage."""
import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db
from lab import Lab


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    pool = db.make_pool()
    pool.open()
    app.state.pool = pool
    app.state.lab = Lab(pool)
    if not app.state.lab.is_built():  # first run only: the index then survives restarts in Postgres
        app.state.lab.build("character", 1000, 0)  # the lab's own settings
    yield
    pool.close()


app = FastAPI(title="RAG Lab", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The request shape and the endpoints:

```python
# needs: your backend folder (file: main.py, append)
class IndexIn(BaseModel):
    splitter: Literal["character", "recursive"] = "character"
    chunk_size: int = Field(default=1000, ge=100, le=3000)
    chunk_overlap: int = Field(default=0, ge=0, le=500)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/chunks")
def chunks(request: Request):
    return request.app.state.lab.state()


@app.post("/api/index")
def index(body: IndexIn, request: Request):
    if body.chunk_overlap >= body.chunk_size:
        raise HTTPException(status_code=422, detail="chunk_overlap must be smaller than chunk_size")
    lab = request.app.state.lab
    lab.build(body.splitter, body.chunk_size, body.chunk_overlap)
    return lab.state()
```

Run it (Postgres up, from `backend/`):

```bash
uv run uvicorn main:app --reload --port 8000
```

The first start takes a few seconds: it downloads the file and embeds 16 chunks. Then:

```bash
curl -s localhost:8000/api/chunks | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['chunks']), [c['length'] for c in d['chunks']][:6])"
curl -s -X POST localhost:8000/api/index -H "Content-Type: application/json" -d '{"chunk_size":200,"chunk_overlap":200}'
```

**What you should see:** `16 [18, 1624, 21, 1885, 28, 1903]` (tiny headings between big chunks), then a `422` error message about the overlap.

**Frontend.** Create `src/lib/api.ts`:

```ts
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Chunk = { id: number; length: number; text: string };
export type Hit = { id: number; score: number; text: string };
export type Turn = { role: "user" | "assistant"; content: string };
export type IndexSettings = { splitter: "character" | "recursive"; chunk_size: number; chunk_overlap: number };

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) {
    // FastAPI sends errors as { detail: ... }.
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const getJson = <T,>(path: string) => send<T>(path);

export const postJson = <T,>(path: string, body: unknown) =>
  send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
```

Create `src/components/chunks-panel.tsx`:

```tsx
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
```

Show it in `src/app/page.tsx` for now:

```tsx
import { ChunksPanel } from "@/components/chunks-panel";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl p-6">
      <ChunksPanel />
    </main>
  );
}
```

Run the frontend (`npm run dev` in `frontend/`) and open http://localhost:3000.

**What you should see:** `16 chunks` as bars. Several are tiny with a red "tiny, probably a lone heading" badge.

### Why it works

The page asks the backend for chunks and draws a bar per chunk, scaled to the longest. Seeing it explains the lab quirk from [Tutorial 1, Concept 3](01-rag-study-guide-and-lab-adapted.md#concept-3-load-and-split-into-chunks): `CharacterTextSplitter` cuts only at blank lines, so a heading and its text end up in different chunks.

### Try it

1. Choose **Recursive**, `chunk_size = 500`, `chunk_overlap = 50`, press **Rebuild index**. How do the bars change?
2. Restart uvicorn. Does the page show the same chunks without re-embedding? (Check the uvicorn log: no new embedding call.)

---

## Step 4: I cannot see what retrieval returns

### The problem

When an answer is wrong you do not know why. Was the right chunk **not retrieved**, or did the LLM **ignore it**? You need to look at retrieval on its own.

### The fix: a search endpoint without the LLM, using a SQL query

```mermaid
flowchart LR
    Q["Question"] --> E["Embed"] --> V["Query vector"]
    V --> S["SELECT ... ORDER BY embedding <=> query LIMIT k"]
    T[("lab_chunks")] --> S
    S --> H["Top-k chunks with scores"]
```

pgvector's `<=>` is the **cosine distance** (0 means the same direction). **Similarity is 1 minus distance.** The whole nearest-neighbour search is one `ORDER BY ... LIMIT`.

### Type this

Add the `search` method **inside the `Lab` class** in `lab.py`, below `state`:

```python
# needs: your backend folder (file: lab.py, append)
    def search(self, question: str, k: int) -> list[dict]:
        vec = np.array(self.embeddings.embed_query(question))
        with self.pool.connection() as conn:
            # <=> is pgvector's cosine DISTANCE (0 = same direction). 1 - distance = similarity.
            rows = conn.execute(
                "SELECT id, content AS text, 1 - (embedding <=> %s) AS score FROM lab_chunks ORDER BY embedding <=> %s LIMIT %s",
                (vec, vec, k),
            ).fetchall()
        return [{**r, "score": round(float(r["score"]), 4)} for r in rows]
```

In `main.py`, add the endpoint:

```python
# needs: your backend folder (file: main.py, append)
class SearchIn(BaseModel):
    question: str = Field(min_length=1)
    k: int = Field(default=4, ge=1, le=10)


@app.post("/api/search")
def search(body: SearchIn, request: Request):
    return {"hits": request.app.state.lab.search(body.question, body.k)}
```

```bash
curl -s -X POST localhost:8000/api/search -H "Content-Type: application/json" -d '{"question":"Can I smoke in company vehicles?","k":3}'
```

**What you should see:** three hits with `id`, `text` and a `score` (for example `0.56`), highest first. The top one is about smoking.

**Frontend.** Create `src/components/search-panel.tsx`:

```tsx
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
```

Put it in a **Tabs** layout together with the chunks panel. Replace `src/app/page.tsx`:

```tsx
"use client";

import { ChunksPanel } from "@/components/chunks-panel";
import { SearchPanel } from "@/components/search-panel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold">RAG Lab: Innovatech Policies</h1>
      <Tabs defaultValue="chunks">
        <TabsList>
          <TabsTrigger value="chunks">1. Chunks</TabsTrigger>
          <TabsTrigger value="search">2. Search</TabsTrigger>
        </TabsList>
        <TabsContent value="chunks" className="pt-4">
          <ChunksPanel />
        </TabsContent>
        <TabsContent value="search" className="pt-4">
          <SearchPanel />
        </TabsContent>
      </Tabs>
    </main>
  );
}
```

**What you should see:** on the Search tab, "Can I smoke in company vehicles?" returns the smoking policy chunk at rank 1 with the highest score.

### Why it works

The question is embedded with the **same** model as the chunks, then Postgres returns the nearest rows. No LLM is called, so it is fast and cheap. The query works because the `<=>` operator is the same one the HNSW index was built for.

### Try it

1. Search the same question after switching to **Recursive** chunks of 500. Do the top chunks get more focused?
2. Search "summarize the document". Are the scores all low? This is why whole-document questions are hard for simple RAG.
3. In psql, run `EXPLAIN SELECT id FROM lab_chunks ORDER BY embedding <=> (SELECT embedding FROM lab_chunks WHERE id = 0) LIMIT 4;` and read the plan. (With only 16 rows Postgres may prefer a plain scan. The index pays off with thousands.)

---

## Step 5: The bot makes things up

### The problem

Ask the lab's own trap question: "Can I eat in company vehicles?" The policies do not say. A plain prompt often answers confidently anyway.

### The fix: an answer endpoint with a switchable "I don't know" rule

```mermaid
flowchart LR
    Q["Question"] --> R["Retrieve top k"] --> P{"Strict rule on?"}
    P -->|"yes"| S["Prompt with I don't know rule"]
    P -->|"no"| L["Plain prompt"]
    S --> M["LLM"]
    L --> M
    M --> A["Answer"]
```

### Type this

Create `backend/qa.py` with the two prompts from the lab and a function that answers. For now it ignores `history` (step 6 uses it):

```python
# needs: your backend folder (file: qa.py)
"""Prompts and the question-answering step. It uses a Lab only to search."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from lab import Lab

# The lab's first prompt has no safety rule. The second is the "I don't know" version.
LOOSE = "Use the context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}"
STRICT = (
    "Use only the context below to answer the question at the end. "
    "If the answer is not in the context, say \"I don't know\". "
    "Do not make up an answer.\n\nContext:\n{context}\n\nQuestion: {question}"
)


def answer(lab: Lab, question: str, k: int, strict: bool, history: list[dict]):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=300)
    hits = lab.search(question, k)
    context = "\n\n".join(h["text"] for h in hits)
    prompt = ChatPromptTemplate.from_template(STRICT if strict else LOOSE)
    reply = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": question})
    return reply, question, hits
```

In `main.py`, add the endpoint. The request already has a `history` field for step 6:

```python
# needs: your backend folder (file: main.py, append)
import qa  # noqa: E402  (move imports to the top of the file if you like)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskIn(SearchIn):
    strict: bool = True
    history: list[Turn] = []


@app.post("/api/ask")
def ask(body: AskIn, request: Request):
    history = [t.model_dump() for t in body.history]
    reply, standalone, hits = qa.answer(request.app.state.lab, body.question, body.k, body.strict, history)
    return {"answer": reply, "standalone_question": standalone, "hits": hits}
```

Try the trap question with the rule on and off:

```bash
curl -s -X POST localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"Can I eat in company vehicles?","strict":false}'
curl -s -X POST localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"Can I eat in company vehicles?","strict":true}'
```

**What you should see** (example): with `"strict": false` the model may answer anyway. With `true` it says `I don't know.`

### Why it works

The only difference between the two prompts is one instruction. That instruction is the lab's whole "Using prompt template" section: trust the context, and decline when it is not there.

### Try it

Send the eat-in-vehicles question with `strict` false, then true. Compare. Which one is grounded?

---

## Step 6: The bot forgets, so we add memory and a chat page

### The problem

After "What is the mobile phone policy?", the follow-up "List the points in it" fails. The retriever searches for the words "List the points in it" and finds nothing relevant.

### The fix: send the history, rewrite the follow-up, then search

```mermaid
sequenceDiagram
    participant P as Ask tab
    participant A as FastAPI
    participant R as Rewriter LLM
    participant D as Postgres
    P->>A: question, history, memory on
    A->>R: rewrite using history
    R->>D: search with the standalone question
    D->>A: top chunks
    A->>P: answer, rewritten question, chunks
```

**Memory off** means the page sends an **empty history**. That is the lab's "see what happens without memory" demo.

### Type this

Replace `backend/qa.py` with a version that uses `history`. It adds a rewrite prompt and one extra model call when there is history:

```python
# needs: your backend folder (file: qa.py)
"""Prompts and the question-answering step. It uses a Lab only to search."""
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from lab import Lab

# The lab's first prompt has no safety rule. The second is the "I don't know" version.
LOOSE = "Use the context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}"
STRICT = (
    "Use only the context below to answer the question at the end. "
    "If the answer is not in the context, say \"I don't know\". "
    "Do not make up an answer.\n\nContext:\n{context}\n\nQuestion: {question}"
)
REWRITE = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's last question so it makes sense on its own, "
               "using the chat history. Return only the question."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])


def answer(lab: Lab, question: str, k: int, strict: bool, history: list[dict]):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=300)
    messages = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
    standalone = question
    if messages:
        standalone = (REWRITE | llm | StrOutputParser()).invoke({"history": messages, "question": question})
    hits = lab.search(standalone, k)
    context = "\n\n".join(h["text"] for h in hits)
    prompt = ChatPromptTemplate.from_template(STRICT if strict else LOOSE)
    reply = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": standalone})
    return reply, standalone, hits
```

`main.py` does not change. Test memory with curl:

```bash
curl -s -X POST localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"List the points in it.","history":[{"role":"user","content":"What is the mobile phone policy?"},{"role":"assistant","content":"It covers phone use at work."}]}'
```

**What you should see:** `standalone_question` in the reply is a full question about the mobile phone policy, and the hits are phone-related.

Now the chat page. Create `src/components/ask-panel.tsx`:

```tsx
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
```

Finish `src/app/page.tsx` with the third tab:

```tsx
"use client";

import { AskPanel } from "@/components/ask-panel";
import { ChunksPanel } from "@/components/chunks-panel";
import { SearchPanel } from "@/components/search-panel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">RAG Lab: Innovatech Policies</h1>
        <p className="text-sm text-muted-foreground">
          Split, search and ask. Change one thing at a time and watch what happens.
        </p>
      </div>
      <Tabs defaultValue="chunks">
        <TabsList>
          <TabsTrigger value="chunks">1. Chunks</TabsTrigger>
          <TabsTrigger value="search">2. Search</TabsTrigger>
          <TabsTrigger value="ask">3. Ask</TabsTrigger>
        </TabsList>
        <TabsContent value="chunks" className="pt-4">
          <ChunksPanel />
        </TabsContent>
        <TabsContent value="search" className="pt-4">
          <SearchPanel />
        </TabsContent>
        <TabsContent value="ask" className="pt-4">
          <AskPanel />
        </TabsContent>
      </Tabs>
    </main>
  );
}
```

**What you should see:** on the Ask tab, ask "What is the mobile phone policy?", then "List the points in it". Under the second answer you see `Searched for: ...` with the rewritten question. Untick **Memory**, repeat, and the second answer gets worse.

### Why it works

The history lives in the browser and goes with every request, because the server keeps no chat. The rewrite step produces a complete question, so the retriever has topic words to match. The "Chunks used" block shows exactly what the model read.

### Try it

1. Tick and untick **Say "I don't know" rule** and ask "Can I eat in company vehicles?".
2. Ask a follow-up with memory off. Open **Chunks used** to see which chunks it fetched.
3. Rebuild the index with **Recursive** and `chunk_size = 500`. Do the answers improve?

---

## Test the real stack

No fakes. With Postgres and the API running, this test uses the real database and the real OpenAI API (a fraction of a cent). Create `backend/test_live.py`:

```python
# needs: your backend folder (file: test_live.py)
"""Live test of the real stack. No fakes.

Needs Postgres running (docker compose up -d postgres) and the API on port 8000
(uv run uvicorn main:app --port 8000, or the whole stack with docker compose up).
It calls the real OpenAI API, so it costs a fraction of a cent.

    uv run python test_live.py
"""
import os

import httpx

API = os.getenv("API_URL", "http://localhost:8000")
client = httpx.Client(base_url=API, timeout=60)


def test_pipeline() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}

    # The lab's own splitter: 16 chunks, and some are lone headings.
    built = client.post("/api/index", json={"splitter": "character", "chunk_size": 1000, "chunk_overlap": 0}).json()
    assert len(built["chunks"]) == 16, len(built["chunks"])
    assert any(c["length"] < 60 for c in built["chunks"]), "expected tiny heading-only chunks"

    # State comes from Postgres, so a second read returns the same thing.
    assert client.get("/api/chunks").json() == built

    hits = client.post("/api/search", json={"question": "Can I smoke in company vehicles?", "k": 3}).json()["hits"]
    assert len(hits) == 3 and hits[0]["score"] > hits[-1]["score"]
    assert "smok" in hits[0]["text"].lower(), hits[0]["text"][:80]

    # A better splitter gives more, smaller chunks, and replaces the old ones.
    better = client.post("/api/index", json={"splitter": "recursive", "chunk_size": 500, "chunk_overlap": 50}).json()
    assert len(better["chunks"]) > 30 and max(c["length"] for c in better["chunks"]) <= 500
    assert client.get("/api/chunks").json()["settings"]["splitter"] == "recursive"
    client.post("/api/index", json={"splitter": "character", "chunk_size": 1000, "chunk_overlap": 0})  # put the lab's settings back


def test_answers() -> None:
    body = {"question": "Can I smoke in company vehicles?", "k": 3, "strict": True}
    smoke = client.post("/api/ask", json=body).json()
    assert "not" in smoke["answer"].lower(), smoke["answer"]

    # The lab's trap question. With the rule on, the model should decline.
    eat = client.post("/api/ask", json={**body, "question": "Can I eat in company vehicles?"}).json()
    assert "know" in eat["answer"].lower(), eat["answer"]

    # Memory: a follow-up with no topic words is rewritten using the history.
    history = [{"role": "user", "content": "What is the mobile phone policy?"}, {"role": "assistant", "content": "It covers phone use at work."}]
    follow = client.post("/api/ask", json={"question": "List the points in it.", "k": 3, "strict": True, "history": history}).json()
    assert "phone" in follow["standalone_question"].lower(), follow["standalone_question"]


def test_validation() -> None:
    assert client.post("/api/index", json={"chunk_size": 200, "chunk_overlap": 200}).status_code == 422
    assert client.post("/api/search", json={"question": "", "k": 3}).status_code == 422
    assert client.post("/api/search", json={"question": "x", "k": 99}).status_code == 422


if __name__ == "__main__":
    for test in (test_pipeline, test_answers, test_validation):
        test()
        print("ok  ", test.__name__)
    print("ALL LIVE TESTS PASSED")
```

```bash
cd course2/module1/my-lab/backend
uv run python test_live.py
```

**What you should see:** `ALL LIVE TESTS PASSED`. It proves, against the real thing: the lab's splitter gives 16 chunks with tiny headings, the state comes back from Postgres, search returns the smoking chunk first, a better splitter replaces the old chunks, the strict rule makes the trap question get "I don't know", and a follow-up is rewritten into a standalone question. It does **not** prove the page looks right (try it by hand). LLM text varies, so the checks look for facts, not exact wording.

---

## Step 7: Run it with Docker

### The problem

To run the app you now need Python and its packages, Node and its packages, a Postgres container, the right environment variables, and several terminals. A friend (or you in six months) will get at least one of those wrong.

### The fix: one command

**Docker** packages each part with everything it needs into an **image**, and **Docker Compose** starts all the parts together from one file. You will write three kinds of files:

| File | Job |
|---|---|
| `backend/Dockerfile` | Recipe for the backend image |
| `frontend/Dockerfile` | Recipe for the frontend image |
| `docker-compose.yml` | Starts and connects the services |

```mermaid
flowchart LR
    C["docker compose up"] --> P[("postgres")] --> B["backend image, port 8000"]
    C --> F["frontend image, port 3000"]
    F -.->|"browser calls"| B
```

### Type this

**1. Pin the backend's packages.** In the Docker image there is no repo-wide environment, so list exactly what the backend needs. Create `backend/requirements.txt`. Pinned versions mean the image builds the same way next year:

```text
# Only what this app needs, pinned to the versions it was tested with.
fastapi==0.143.3
uvicorn[standard]==0.54.0
langchain-core==1.6.10
langchain-openai==1.7.2
langchain-text-splitters==1.1.3
python-dotenv==1.2.4
pydantic==2.14.1
httpx==0.28.1
numpy==2.5.4
psycopg[binary]==3.3.6
psycopg-pool==3.3.3
pgvector==0.5.1
```

**2. The backend Dockerfile.** Create `backend/Dockerfile`. Read it in four pieces. Type them one after another into the same file.

Start from a small Python image and set sane defaults:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
```

Install the dependencies **before** copying your code. Docker caches each step as a layer, so when you edit code, the slow `pip install` layer is reused:

```dockerfile
# Install dependencies first, so code changes do not reinstall everything.
COPY requirements.txt .
RUN pip install -r requirements.txt
```

Do not run as root. If someone breaks into the app, a normal user can do far less damage. Then copy the code:

```dockerfile
# Run as a normal user, not root. DATA_DIR is the volume mount point.
RUN useradd --create-home --uid 10001 app && mkdir /data && chown app /data
COPY --chown=app . .
USER app
```

Say which port it uses, how Docker can tell it is healthy, and how to start it. `--host 0.0.0.0` is needed so the app accepts connections from outside the container:

```dockerfile
ENV DATA_DIR=/data
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add `backend/.dockerignore` so junk does not get copied into the image:

```text
__pycache__/
*.pyc
data/
.env
```

**3. The frontend Dockerfile.** Create `frontend/Dockerfile`. It has **three stages**. Only the last one becomes the final image, so build tools never ship.

Stage 1 installs packages. `npm ci` installs exactly what `package-lock.json` says:

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
```

Stage 2 builds the app. Read the comment: a `NEXT_PUBLIC_*` value is **written into the JavaScript when you build**, so it must be the address your *browser* uses:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* values are written into the JavaScript at build time. This is the address
# the BROWSER uses to reach the API, so it is localhost, not the Docker service name.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build
```

Stage 3 is the small runtime image. It copies only the built server, runs as a normal user and has a health check:

```dockerfile
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN addgroup -S -g 10001 app && adduser -S -u 10001 -G app app
# The standalone output holds the server and only the packages it needs.
COPY --from=build --chown=app:app /app/.next/standalone ./
COPY --from=build --chown=app:app /app/.next/static ./.next/static
COPY --from=build --chown=app:app /app/public ./public
USER app
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
```

This needs one setting in `frontend/next.config.ts`, which makes Next.js produce a small self-contained server in `.next/standalone`:

```ts
  output: "standalone",
```

(Add that line inside the `nextConfig` object.) Create `frontend/.dockerignore`:

```text
node_modules
.next
.env*
npm-debug.log
Dockerfile
```

**4. Keep the secret out of the files.** Create `.env.example` and copy it to `.env` (git ignores `.env`):

```bash
cp .env.example .env   # then put your OpenAI key in .env
```

```text
# Copy this file to .env and fill in your key:  cp .env.example .env
OPENAI_API_KEY=sk-...
```

**5. The compose file.** Create `docker-compose.yml`. It has three services. `postgres` uses a ready-made image. The other two are built from your Dockerfiles.

```yaml
name: rag-lab   # a fixed project name, so volumes do not clash with the other apps in this repo

services:
  postgres:
    image: pgvector/pgvector:pg17   # Postgres with the pgvector extension installed
    environment:
      POSTGRES_USER: lab
      POSTGRES_PASSWORD: lab
      POSTGRES_DB: lab
    ports:
      - "5432:5432"   # published so you can also run the API on your machine; remove for a locked-down setup
    volumes:
      - pgdata:/var/lib/postgresql/data   # keeps the index when the container restarts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lab"]
      interval: 3s
      retries: 20
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:?Set OPENAI_API_KEY in app/.env (copy .env.example)}
      DATABASE_URL: postgresql://lab:lab@postgres:5432/lab   # "postgres" is the service name on the Docker network
      FRONTEND_ORIGINS: http://localhost:3000,http://127.0.0.1:3000
    ports:
      - "8000:8000"
    volumes:
      - lab-data:/data   # keeps the downloaded policy file between restarts
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000   # the address the browser uses
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

volumes:
  pgdata:
  lab-data:
```

What the important lines do:

| Line | Why |
|---|---|
| `name:` | A fixed project name, so this app's volumes never mix with another app's. |
| `${OPENAI_API_KEY:?...}` | Reads the key from `.env`. If it is missing, compose stops with your message instead of failing later. |
| `depends_on ... service_healthy` | Start order that waits for a *healthy* service, not just a started one. |
| `volumes` | Data that must outlive the container. |
| `restart: unless-stopped` | Restart after a crash or a reboot. |
| `NEXT_PUBLIC_API_URL` under `args` | Passed to the frontend **build**, as explained above. |
| `pgdata` volume | The database files live outside the container, so the index survives `docker compose down`. |
| `lab-data` volume | Keeps the downloaded policy file. |
| `DATABASE_URL` with host `postgres` | Inside Docker, the database is reached by its service name. |

### Run it

```bash
cd course2/module1/my-lab
docker compose up --build
```

In another terminal:

```bash
docker compose ps                 # every service should say healthy
docker compose logs -f backend    # follow one service's log
docker compose exec backend id -u # 10001: not root
```

Open http://localhost:3000. Run the live test against the container:

```bash
cd course2/module1/my-lab/backend
uv run python test_live.py
```

**What you should see:** every service `healthy`, the page loads, and `ALL LIVE TESTS PASSED`. Stop with `docker compose down` (add `-v` to also delete the volumes).

### Why it works

The image holds the code and its exact dependencies, so it behaves the same on any machine. Compose gives the services a private network where they find each other by service name (the backend reaches the database at `postgres:5432`). The **browser**, though, is outside that network, which is why `NEXT_PUBLIC_API_URL` says `localhost:8000` and not a service name.

### Common Docker mistakes

| Mistake | What you see | Fix |
|---|---|---|
| Missing `.env` | `Set OPENAI_API_KEY in app/.env` | Copy `.env.example` to `.env` and add your key. |
| Used a service name in `NEXT_PUBLIC_API_URL` | The page loads but every call fails in the browser console | Use the address the browser uses, `http://localhost:8000`, then rebuild. |
| Changed `NEXT_PUBLIC_API_URL` without rebuilding | The old address is still used | `docker compose up --build`. |
| Code change not showing | Old behaviour | Rebuild with `--build`. |
| `address already in use` | A port is taken | Stop the other app (these apps share ports 3000, 8000 and 5432), or change the left side of the port mapping. |
| `ModuleNotFoundError` in the container | Backend unhealthy | The package is missing from `requirements.txt`. Add it with a pinned version and rebuild. |
| `npm ci` fails | Build stops in stage 1 | `package.json` and `package-lock.json` disagree. Run `npm install` locally and commit both. |
| Backend `unhealthy` on first start | `docker compose ps` | Read `docker compose logs backend`. The health check only says something is wrong. |

---

## The whole app

```mermaid
flowchart TB
    subgraph Browser["Next.js, port 3000"]
        T1["Chunks tab"]
        T2["Search tab"]
        T3["Ask tab"]
    end
    subgraph Server["FastAPI, port 8000"]
        E1["POST /api/index, GET /api/chunks"]
        E2["POST /api/search"]
        E3["POST /api/ask"]
        L["Lab: build, state, search"]
        Q["qa: prompts, rewrite, answer"]
    end
    PG[("Postgres + pgvector: lab_chunks, lab_settings")]
    T1 --> E1 --> L
    T2 --> E2 --> L
    T3 -->|"question, history, strict, k"| E3 --> Q --> L
    L --> PG
    L --> O["OpenAI embeddings"]
    Q --> C["OpenAI chat"]
```

| Lab section | Where |
|---|---|
| Load the document | `load_policies` |
| Splitting into chunks | `Lab.build`, Chunks tab |
| Embedding and storing | `Lab.build` writes to the `lab_chunks` table (pgvector replaces Chroma) |
| LLM model | `ChatOpenAI` inside `qa.answer` |
| Retrieval (`RetrievalQA`) | `Lab.search` (SQL) plus the prompt in `qa.answer` |
| Prompt template | `LOOSE` and `STRICT` |
| Memory | `history` and `REWRITE` |
| Exercise 2: return the source | the "Chunks used" block |

## Common mistakes

| Mistake | What you see | Fix |
|---|---|---|
| Postgres not running | `connection refused` when uvicorn starts | `docker compose up -d`, wait for the health check. |
| Port 5432 already used | `docker compose up` fails | Stop the other Postgres (for example the OWASP chat app's), or change the left side of `"5432:5432"` and `DATABASE_URL`. |
| Vector size mismatch | `expected 1536 dimensions, not 3072` | The `vector(N)` column and the embedding model must agree. |
| `type "vector" does not exist` | Error on startup | Use the `pgvector/pgvector` image and keep `CREATE EXTENSION` in `schema.sql`. |
| Registered pgvector before the extension existed | `vector type not found in the database` | Run `init_schema()` before opening the pool. |
| Backend not running | "Cannot reach the backend" or `Failed to fetch` | Start `uv run uvicorn main:app --reload --port 8000`. |
| CORS missing | "blocked by CORS policy" | Allow `http://localhost:3000` in the middleware. |
| Port 3000 used by the module 2 app | Next.js picks another port, and CORS blocks it | Stop the other app, or add the new port to `FRONTEND_ORIGINS`. |
| Overlap not smaller than size | `422` with a message | Lower the overlap. |
| Changed splitter settings but old results | Stale chunks | `build` deletes all rows first. Check it ran in a transaction. |
| Missing API key | `500` with `api_key` in the log | Put `OPENAI_API_KEY` in the root `.env`, restart uvicorn. |

## Practice

No answers shown. Ask me for a hint.

1. **Your own file.** The lab's Exercise 1 gives a second document (`XVnuuEg94sAE4S_xAsGxBA.txt`). Add a way to switch documents. What must change in the tables so two documents can coexist?
2. **Show the file position.** Store each chunk's start position in a new column and show it in the Chunks tab.
3. **Score cutoff.** In `/api/ask`, return "I don't know" without the LLM if the best score is below a number. Where should the number live?
4. **Another model.** The lab's Exercise 3 swaps the model. Add a model dropdown (allow-list it on the server). What breaks if the new embedding model has a different size?
5. **Compare splitters.** For three questions, record the top chunk id for Character and Recursive. Which splitter finds the right chunk more often? Why?
6. **Do we need Redis?** Name one feature that would make you add it here (hint: look at what the OWASP chat uses it for).
7. **Explain it.** In six sentences, tell a friend what each tab shows about the RAG pipeline.

## Cheat sheet

| Step | Problem | Added |
|---|---|---|
| 0 | Nothing runs yet | Hello world: one endpoint, one page |
| 1 | Nowhere to keep vectors | Postgres with pgvector in Docker |
| 2 | Pipeline in cells | `schema.sql`, `db.py`, `Lab` class |
| 3 | Chunks invisible | `/api/index`, `/api/chunks`, Chunks tab |
| 4 | Retrieval invisible | `Lab.search` (SQL, `<=>`), `/api/search`, Search tab |
| 5 | Makes things up | `STRICT` vs `LOOSE` prompt in `qa.py`, `/api/ask` |
| 6 | Forgets | history plus `REWRITE`, Ask tab |
| 7 | Hard to run | Dockerfiles and compose, one command |

Back to [Tutorial 1](01-rag-study-guide-and-lab-adapted.md) or [Tutorial 2](02-rag-build-a-notes-bot.md).
