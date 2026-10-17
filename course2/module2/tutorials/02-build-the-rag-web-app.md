# Tutorial 2: Build a RAG Web App (Next.js + FastAPI)

**What you build.** A web app where you chat with your own documents. It has a chat window, a settings panel (model, number of chunks, answer style, show sources), and a box to upload more `.txt` or `.md` files. The brain is the RAG notes bot from [module 1](../../module1/tutorials/02-rag-build-a-notes-bot.md). Here we give it a proper web interface instead of a Gradio page.

**How this tutorial works.** One app, grown in small steps. Each step starts with a **problem** you just hit, then the **fix**.

New to the Gradio-to-web mapping? Read [Tutorial 1](01-gradio-concepts-adapted-to-nextjs.md) first. It covers endpoints, `fetch`, CORS and the shadcn inputs that this tutorial reuses.

## The path

```mermaid
flowchart LR
    S1["1 RAG logic stuck in a notebook"] --> S2["2 Cannot ask over HTTP"]
    S2 --> S3["3 No chat page"]
    S3 --> S4["4 Cannot add my own files"]
    S4 --> S5["5 Server forgets the chat"]
    S5 --> S6["6 Cannot see sources"]
    S6 --> S7["7 No way to tune it"]
    S7 --> S8["8 Errors look like nothing"]
```

## Before you start

- Tutorial 1 setup done, or use the finished project in [../app/](../app/).
- `OPENAI_API_KEY` in the repo-root `.env`.
- Work in `course2/module2/my-app/` (build your own) and compare with `app/` when stuck.
- Packages `fastapi`, `uvicorn` and `python-multipart` are in the root `pyproject.toml`. Frontend packages come from `npm install`.

Real API calls cost a few cents in total. The checks at the end of this tutorial use fake models and cost nothing.

---

## Step 1: The RAG logic is stuck in a notebook

### The problem

In module 1 the splitter, embeddings, vector store and prompts were loose notebook cells. A web server cannot run cells. It needs one clean object with simple methods: **add text** and **ask a question**.

### The fix: a `RagEngine` class with no web code in it

Keeping RAG separate from the web layer means you can test and change each on its own.

```mermaid
flowchart LR
    W["Web layer: main.py"] --> E["RagEngine: rag.py"]
    E --> V[("Vector store")]
    E --> L["LLM"]
```

### Type this

Create `backend/rag.py`. First the imports and the prompt:

```python
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    "Answer using only the context. If the answer is not in the context, "
    "say \"I don't know\". {style}\n\nContext:\n{context}\n\nQuestion: {question}"
)
STYLES = {
    "concise": "Answer in one or two sentences.",
    "detailed": "Answer in a short paragraph with the key details.",
}
```

Then the class with its two jobs, **add text** (indexing) and **ask** (query):

```python
class RagEngine:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.store = InMemoryVectorStore(self.embeddings)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100, add_start_index=True
        )
        self.sources: dict[str, int] = {}  # file name -> number of chunks

    def add_text(self, name: str, text: str) -> int:
        doc = Document(page_content=text, metadata={"source": name})
        chunks = self.splitter.split_documents([doc])
        self.store.add_documents(chunks)
        self.sources[name] = self.sources.get(name, 0) + len(chunks)
        return len(chunks)

    def ask(self, question: str, k: int, model: str, style: str):
        llm = ChatOpenAI(model=model, temperature=0, max_tokens=400)
        docs = self.store.as_retriever(search_kwargs={"k": k}).invoke(question)
        context = "\n\n".join(d.page_content for d in docs)
        chain = ANSWER_PROMPT | llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question, "style": STYLES[style]})
        return answer, docs
```

Try the engine by itself:

```python
engine = RagEngine()
print(engine.add_text("policy.txt", "Smoking is not permitted in company vehicles. " * 30))
answer, docs = engine.ask("Can I smoke in the car?", k=2, model="gpt-4o-mini", style="concise")
print(answer, len(docs))
```

**What you should see** (example): a number such as `3` (chunks added), then an answer like `No, smoking is not permitted in company vehicles.` and `2`.

### Why it works

`add_text` is the **indexing** phase (split, embed, store). `ask` is the **query** phase (retrieve, build the prompt, answer). Both are the same ideas as module 1, now wrapped in a class.

### Try it

Change `chunk_size` to `200` and see how many chunks `add_text` returns for the same text.

---

## Step 2: Nothing can ask over HTTP

### The problem

The engine works in Python, but a browser cannot call a Python method. We need a **web address** for it.

### The fix: a FastAPI endpoint, with validation

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as FastAPI
    participant E as RagEngine
    B->>A: POST /api/ask with question, k, model, style
    A->>A: validate the JSON
    A->>E: ask(...)
    E-->>A: answer and chunks
    A-->>B: JSON reply
```

### Type this

Create `backend/main.py`:

```python
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ALLOWED_MODELS = {"gpt-4o-mini", "gpt-4o"}

app = FastAPI(title="RAG Notes Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One engine for the whole server, so uploaded documents stay in memory.
rag_engine = RagEngine()
```

At the top of `main.py` also add `from rag import RagEngine`.

Describe what a question looks like. `Field(ge=1, le=10)` limits `k` to 1 through 10:

```python
class AskIn(BaseModel):
    question: str = Field(min_length=1)
    k: int = Field(default=4, ge=1, le=10)
    model: str = "gpt-4o-mini"
    style: Literal["concise", "detailed"] = "concise"
```

And the endpoint:

```python
@app.post("/api/ask")
def ask_endpoint(body: AskIn):
    if body.model not in ALLOWED_MODELS:
        raise HTTPException(status_code=422, detail=f"model must be one of {sorted(ALLOWED_MODELS)}")
    answer, docs = rag_engine.ask(body.question, body.k, body.model, body.style)
    return {"answer": answer, "sources": [d.page_content for d in docs]}
```

Run the server (from the repo environment) and open http://localhost:8000/docs:

```bash
cd course2/module2/my-app/backend
uv run uvicorn main:app --reload --port 8000
```

Or test in Python without a server:

```python
from fastapi.testclient import TestClient

client = TestClient(app)
r = client.post("/api/ask", json={"question": "Can I smoke in the car?", "k": 2})
print(r.status_code, r.json()["answer"])
print(client.post("/api/ask", json={"question": "x", "k": 50}).status_code)
print(client.post("/api/ask", json={"question": "x", "model": "gpt-9"}).status_code)
```

**What you should see:** `200` and an answer, then `422`, then `422`.

### Why it works

FastAPI turns your function into an endpoint and `AskIn` into the contract. A bad `k`, an empty question or a wrong `style` is rejected **before** your code runs. The `ALLOWED_MODELS` check matters too: without it, a user could ask the server to run any model name, at your cost.

### Try it

Open `/docs`, click **POST /api/ask**, **Try it out**, and send a request by hand.

---

## Step 3: There is no chat page

### The problem

We have an API but no page. Time for the frontend.

### The fix: a chat component that calls the endpoint

```mermaid
flowchart LR
    T["Textarea"] -->|"Enter"| C["send function"] -->|"POST"| A["/api/ask"] --> M["messages list"] --> U["Chat bubbles"]
```

### Type this

You need `src/lib/api.ts` from Tutorial 1 (`postJson`). Add the types to it:

```ts
export type Turn = { role: "user" | "assistant"; content: string };
export type Source = { source: string; start_index: number; text: string };
```

We will start with the simplest chat: question in, answer out. Create `src/components/chat-panel.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { postJson, type Settings } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export function ChatPanel({ settings }: { settings: Settings }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    const q = question.trim();
    if (!q || busy) return;
    setBusy(true);
    setQuestion("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    try {
      const data = await postJson<{ answer: string }>("/api/ask", {
        question: q,
        k: settings.k,
        model: settings.model,
        style: settings.style,
      });
      setMessages((m) => [...m, { role: "assistant", content: data.answer }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {messages.map((m, i) => (
        <Card key={i} className={m.role === "user" ? "bg-muted" : ""}>
          <CardContent className="text-sm">
            <p className="font-medium">{m.role === "user" ? "You" : "Bot"}</p>
            <p className="whitespace-pre-wrap">{m.content}</p>
          </CardContent>
        </Card>
      ))}
      <Textarea value={question} placeholder="Ask about your notes..." onChange={(e) => setQuestion(e.target.value)} />
      <Button onClick={send} disabled={busy}>
        {busy ? "Thinking..." : "Ask"}
      </Button>
    </div>
  );
}
```

It needs a `Settings` type and the settings panel from Tutorial 1, Concept 5. Add the page. Replace `src/app/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/chat-panel";
import { SettingsPanel } from "@/components/settings-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Settings } from "@/lib/api";

export default function Home() {
  const [settings, setSettings] = useState<Settings>({
    model: "gpt-4o-mini",
    k: 4,
    style: "concise",
    showSources: true,
  });

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold">RAG Notes Bot</h1>
      <div className="grid gap-6 md:grid-cols-[1fr_18rem]">
        <ChatPanel settings={settings} />
        <Card>
          <CardHeader>
            <CardTitle>Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <SettingsPanel value={settings} onChange={setSettings} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
```

Start `npm run dev` and open http://localhost:3000. The knowledge base is empty at this point, so first add some text with the upload box in step 4, or index it from Python as you did in Step 1.

**What you should see:** a chat box. Ask something and an answer appears under "Bot".

### Why it works

`useState` holds the list of messages. When state changes, React redraws. `send` adds your message, calls the API, then adds the reply. `"use client"` is needed because this component reacts to clicks.

### Try it

Press **Ask** with an empty box. Why does nothing happen? (Look for `if (!q || busy) return;`.)

---

## Step 4: I cannot add my own files

### The problem

The bot only knows what you indexed from Python. A user needs an upload box.

### The fix: an upload endpoint and a documents panel

```mermaid
flowchart LR
    P["File picker"] -->|"FormData"| U["POST /api/documents"] --> S["split, embed, store"] --> R["chunks per file"]
```

### Type this

**Backend.** Add to `main.py` (the `UploadFile` pieces are from Tutorial 1, Concept 4):

```python
from typing import Annotated

from fastapi import File, UploadFile


@app.get("/api/documents")
def list_documents():
    return {"sources": rag_engine.sources}


@app.post("/api/documents")
async def add_documents(files: Annotated[list[UploadFile], File()]):
    added = {}
    for f in files:
        text = (await f.read()).decode("utf-8", errors="ignore")
        added[f.filename] = rag_engine.add_text(f.filename, text)
    return {"added": added, "sources": rag_engine.sources}
```

```python
files = [("files", ("rules.txt", b"Visitors must sign in at reception. " * 40))]
print(client.post("/api/documents", files=files).json()["added"])
print(client.get("/api/documents").json()["sources"])
```

**What you should see:** `{'rules.txt': 2}` (the number may differ) and a dictionary of file names with chunk counts.

**Frontend.** Add `postFiles` and `getJson` to `src/lib/api.ts`:

```ts
export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json() as Promise<T>;
}
```

(`postFiles` is from Tutorial 1, Concept 4.) Create `src/components/documents-panel.tsx`:

```tsx
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
```

Add a second card under Settings in `page.tsx`:

```tsx
<Card>
  <CardHeader>
    <CardTitle>Knowledge base</CardTitle>
  </CardHeader>
  <CardContent>
    <DocumentsPanel />
  </CardContent>
</Card>
```

(Import `DocumentsPanel`, and wrap the two cards in a `<div className="space-y-6">`.)

**What you should see:** pick a `.md` file. The badge shows `yourfile.md: 12 chunks`. Ask a question about it.

### Why it works

The file goes through the same `add_text` as Step 1. The module-1 file `transcript.md` is a good first upload, because it is your own study material.

### Beyond the video: pre-load your notes

Instead of uploading by hand each time, you can pre-load `course2/module1/transcript.md` the first time the server needs the engine. The finished app in `app/backend/main.py` does exactly that with a small `seed()` method. Try writing it yourself in the Practice section.

> The index lives **in memory**. When uvicorn restarts (including `--reload`), uploads are gone. A real app would use a database such as Chroma or FAISS saved to disk.

### Try it

Upload the same file twice. What happens to the chunk count and to the answers? (Think about duplicates.)

---

## Step 5: The server forgets the conversation

### The problem

Ask "What is cosine similarity?" and then "How is it different from the dot product?". The second question has no topic words. The retriever searches with "it" and finds nothing useful.

### The fix: the page sends the history, the server rewrites the follow-up

HTTP servers forget everything between requests. The simplest memory is to keep the chat in the **browser** and send it with every question. The server rewrites the follow-up into a standalone question, then searches.

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as FastAPI
    participant R as Rewriter LLM
    participant S as Retriever
    B->>A: question + history
    A->>R: rewrite using history
    R->>S: standalone question
    S->>A: top chunks
    A->>B: answer
```

### Type this

**Backend, `rag.py`.** Add these imports at the top and the rewrite prompt:

```python
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's last question so it makes sense on its own, "
               "using the chat history. Return only the question."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])
```

Replace the whole `RagEngine` class with this version. Only `ask` changed: it takes `history` and rewrites follow-ups first.

```python
# needs: replaces the RagEngine class from Step 1 in your rag.py
class RagEngine:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.store = InMemoryVectorStore(self.embeddings)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100, add_start_index=True
        )
        self.sources: dict[str, int] = {}

    def add_text(self, name: str, text: str) -> int:
        doc = Document(page_content=text, metadata={"source": name})
        chunks = self.splitter.split_documents([doc])
        self.store.add_documents(chunks)
        self.sources[name] = self.sources.get(name, 0) + len(chunks)
        return len(chunks)

    def ask(self, question: str, history: list[dict], k: int, model: str, style: str):
        llm = ChatOpenAI(model=model, temperature=0, max_tokens=400)
        messages = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
        # Rewrite follow-ups so the retriever searches with a complete question.
        standalone = question
        if messages:
            standalone = (REWRITE_PROMPT | llm | StrOutputParser()).invoke({"history": messages, "question": question})
        docs = self.store.as_retriever(search_kwargs={"k": k}).invoke(standalone)
        context = "\n\n".join(d.page_content for d in docs)
        chain = ANSWER_PROMPT | llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": standalone, "style": STYLES[style]})
        return answer, docs
```

**Backend, `main.py`.** Add a `Turn` model, a `history` field on `AskIn`, and pass it on. Replace `AskIn` and the endpoint:

```python
# needs: replaces AskIn and ask_endpoint from Step 2 in your main.py
class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskIn(BaseModel):
    question: str = Field(min_length=1)
    history: list[Turn] = []
    k: int = Field(default=4, ge=1, le=10)
    model: str = "gpt-4o-mini"
    style: Literal["concise", "detailed"] = "concise"


@app.post("/api/ask")
def ask_endpoint(body: AskIn):
    if body.model not in ALLOWED_MODELS:
        raise HTTPException(status_code=422, detail=f"model must be one of {sorted(ALLOWED_MODELS)}")
    history = [t.model_dump() for t in body.history]
    answer, docs = rag_engine.ask(body.question, history, body.k, body.model, body.style)
    return {"answer": answer, "sources": [d.page_content for d in docs]}
```

```python
# needs: your updated engine and endpoint from above, running in your own project
history = [{"role": "user", "content": "What is cosine similarity?"}, {"role": "assistant", "content": "It compares direction."}]
r = client.post("/api/ask", json={"question": "How is it different from the dot product?", "history": history})
print(r.status_code)
```

**What you should see:** `200`.

**Frontend, `chat-panel.tsx`.** Two small changes. Add `history` before you add the new message, and send it:

```tsx
    // The server keeps no chat state, so we send the history with every question.
    const history = messages.map(({ role, content }) => ({ role, content }));
```

Put it right after `setQuestion("")`. Then add `history,` to the object you pass to `postJson` (next to `question: q,`).

**What you should see:** ask about a topic, then follow up using "it". The second answer stays on topic.

### Why it works

The **rewrite** step turns "How is it different?" into "How is cosine similarity different from the dot product?". Only then does the retriever search. That is exactly module 1, Concept 8, now across a network.

### Try it

Press F12, open the **Network** tab and look at the `ask` request. Find `history` in the payload. How does it grow after each turn?

---

## Step 6: I cannot see where the answer came from

### The problem

RAG should be **verifiable**. Right now the API returns only text for the sources, with no file name or position.

### The fix: return source details, show them in a collapsible block

### Type this

**Backend.** Return more fields from the endpoint. Replace the `return` line of `ask_endpoint`:

```python
# needs: replaces the return line inside ask_endpoint in your main.py
    return {
        "answer": answer,
        "sources": [
            {"source": d.metadata["source"], "start_index": d.metadata["start_index"], "text": d.page_content}
            for d in docs
        ],
    }
```

`start_index` exists because we set `add_start_index=True` in the splitter (Step 1).

**Frontend.** In `chat-panel.tsx`:

1. Import the type: `import { postJson, type Settings, type Source } from "@/lib/api";`
2. Let a message carry sources: `type Message = { role: "user" | "assistant"; content: string; sources?: Source[] };`
3. Read them from the response: `postJson<{ answer: string; sources: Source[] }>(...)` and `{ role: "assistant", content: data.answer, sources: data.sources }`.
4. Show them below the answer text, inside the same `CardContent`:

```tsx
{settings.showSources && m.sources && (
  <details>
    <summary className="cursor-pointer text-muted-foreground">Sources ({m.sources.length})</summary>
    <ul className="mt-2 space-y-2">
      {m.sources.map((s, j) => (
        <li key={j} className="rounded border p-2">
          <span className="text-xs text-muted-foreground">
            {s.source} at character {s.start_index}
          </span>
          <p className="mt-1 line-clamp-4">{s.text}</p>
        </li>
      ))}
    </ul>
  </details>
)}
```

**What you should see:** under each bot answer, a "Sources (4)" row. Click it to see the chunks with file name and position.

### Why it works

The retriever already returned the chunks. We simply stopped throwing their metadata away. The checkbox in Settings (`showSources`) hides or shows the block without another request.

### Try it

Ask something the notes do not cover. Do the sources look related? What does that tell you about the bot's "I don't know"?

---

## Step 7: There is no way to tune it

### The problem

The answers are sometimes thin. In module 1 you learned the knobs: `k`, the model and the prompt. Users should be able to turn them.

### The fix: use the settings that are already in the request

Nothing new to write. Look at what you already built:

| Control (Tutorial 1, Concept 5) | Sent as | Backend rule |
|---|---|---|
| Slider | `k` | `Field(ge=1, le=10)` |
| Dropdown | `model` | must be in `ALLOWED_MODELS` |
| Radio | `style` | `Literal["concise", "detailed"]` |
| Checkbox | not sent | only hides sources in the page |

### Try it

1. Ask the same question with `k = 1` and then `k = 8`. Which answer is better? Which costs more?
2. Switch the style from concise to detailed.
3. In the browser tools, change the request by hand to `k: 50`. Read the `422` message.

**What you should see:** low `k` can give "I don't know" for answerable questions. High `k` gives fuller but slower answers. This is the retrieval trade-off from module 1, Concept 7.

---

## Step 8: Errors look like nothing happened

### The problem

If the API returns an error (bad key, model name, network), the chat shows nothing. Users think the app froze.

### The fix: catch the error and show it in the chat

In `chat-panel.tsx`, add a `catch` between `try` and `finally` in `send`:

```tsx
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${(e as Error).message}` }]);
    } finally {
```

The `postJson` helper already turns FastAPI's `detail` into the error message (Tutorial 1, Concept 2).

**What you should see:** stop the backend, ask a question, and you get `Error: Failed to fetch` in the chat instead of silence.

### Test the backend without spending money

The finished project has `app/backend/test_api.py`. It replaces the OpenAI classes with fakes, so it is free and runs offline:

```bash
cd course2/module2/app/backend
uv run python -c "import test_api; test_api.test_all(); print('ok')"
```

It checks every endpoint, validation and the `422` cases. It does **not** prove the answers are good, because the fake model always says `fake answer`.

---

## The whole app

```mermaid
flowchart TB
    subgraph Browser["Browser, Next.js on port 3000"]
        CH["ChatPanel"]
        SP["SettingsPanel"]
        DP["DocumentsPanel"]
    end
    subgraph Server["FastAPI on port 8000"]
        AK["POST /api/ask"]
        DC["GET and POST /api/documents"]
        RE["RagEngine"]
    end
    SP --> CH
    CH -->|"question, history, settings"| AK
    DP -->|"files"| DC
    AK --> RE
    DC --> RE
    RE --> VS[("In-memory vector store")]
    RE --> OA["OpenAI: embeddings and chat"]
```

Where each idea from the course lives:

| Course idea | Where |
|---|---|
| Chunking | `RagEngine.__init__` (splitter) and `add_text` |
| Embedding and vector store | `InMemoryVectorStore(self.embeddings)` |
| Retrieval, top-k | `as_retriever(search_kwargs={"k": k})` |
| Augmented prompt | `ANSWER_PROMPT` |
| "I don't know" rule | the instruction inside `ANSWER_PROMPT` |
| Memory | history from the page plus `REWRITE_PROMPT` |
| Sources | `start_index` metadata |
| Gradio interface | `ChatPanel`, `SettingsPanel`, `DocumentsPanel` |

---

## Common mistakes

| Mistake | What you see | Fix |
|---|---|---|
| Backend not running | `Failed to fetch` in the page | Start `uv run uvicorn main:app --reload --port 8000`. |
| CORS missing | "blocked by CORS policy" in the console | `CORSMiddleware` with `http://localhost:3000`. |
| Missing API key | `500` and `api_key` in the backend log | Put `OPENAI_API_KEY` in the root `.env`, restart uvicorn. |
| Uploaded files vanish | Badges empty after a code change | The store is in memory. `--reload` restarts it. Upload again. |
| Set `Content-Type` on upload | Parse error or "no files" | Do not set it for `FormData`. |
| `422` on `/api/ask` | Error text in chat | `k` outside 1 to 10, empty question, or unknown model. |
| Forgot to send `history` | Follow-ups fail | Check the request payload in the Network tab. |
| Server Component error | Message about `useState` | The file needs `"use client"` on the first line. |
| Ran uvicorn with another Python | `No module named fastapi` | Use `uv run` inside the repo. |

## Practice

No answers shown. Ask me for a hint.

1. **Seed method.** Add `seed()` to `RagEngine` that loads `course2/module1/transcript.md` once, and call it the first time `/api/documents` or `/api/ask` is used. Why load lazily instead of at import time?
2. **Score cutoff.** Use `similarity_search_with_score`. If the best score is below a number you choose, return `"I don't know"` without calling the LLM. Where would the number live: the page or the server?
3. **Streaming (stretch).** Make answers appear word by word. Which FastAPI response class would you look at?
4. **Persistence.** Replace `InMemoryVectorStore` with a store that survives restarts. What must change in `add_text`?
5. **Delete a file.** Add `DELETE /api/documents/{name}`. What does the vector store need to support it?
6. **Explain it.** In six sentences, walk through what happens from pressing **Ask** to seeing an answer. Name each box in the whole-app diagram once.

## Cheat sheet

| Step | Problem | What was added |
|---|---|---|
| 1 | Logic stuck in a notebook | `RagEngine` class |
| 2 | No web address | `POST /api/ask` with validation |
| 3 | No page | `ChatPanel` |
| 4 | Cannot add files | `/api/documents` and `DocumentsPanel` |
| 5 | Forgets the chat | history from the page plus a rewrite step |
| 6 | Cannot verify | sources with file name and position |
| 7 | Cannot tune | settings controls tied to validated fields |
| 8 | Silent errors | `catch` and a friendly message |

Back to [Tutorial 1](01-gradio-concepts-adapted-to-nextjs.md).
