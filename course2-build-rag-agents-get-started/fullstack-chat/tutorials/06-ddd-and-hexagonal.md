# Tutorial 6: Refactor to Domain-Driven Design and Hexagonal Architecture

**What you build.** The same OWASP chatbot, with the same behaviour and the same HTTP API, reorganised into two **bounded contexts** (*Conversation* and *Knowledge*), each built as a **hexagon** (domain in the middle, ports around it, adapters on the outside). The frontend does not change at all. The live test from part 4 passes **unchanged**. That is how you know a refactoring worked.

This is a learning exercise, so you will feel the problem first, then fix it one step at a time. Everything stays real: real Postgres, Redis, Celery worker and OpenAI. No fakes.

This is part 6 of 6. Start from the finished app of [part 5](05-docker-compose.md) (`app/`). The finished result of this tutorial is in [../app-hexagonal/](../app-hexagonal/).

| Part | Adds |
|---|---|
| [1](01-hello-world-to-streaming-chat.md) to [5](05-docker-compose.md) | Streaming chat, Postgres, pgvector RAG, Redis and Celery, Docker |
| **6** | **Domain-driven design and hexagonal architecture** |

## The words you will use

| Word | Plain meaning |
|---|---|
| **Domain** | The business rules, written in plain Python with no technology in it. |
| **Bounded context** | A part of the system with its own words and its own model. Inside it, a word means one thing. |
| **Ubiquitous language** | The same words in the conversation with the business, in the code and in the tests. |
| **Entity** | A thing with an identity that changes over time (a Conversation, a Document). |
| **Value object** | A thing defined only by its values (a Source, a Message). Immutable. |
| **Use case** (application service) | One thing a user can do ("send a message"). It orchestrates the domain through ports. |
| **Port** | An interface, owned by the application, saying what it needs ("something that stores chunks"). |
| **Adapter** | Code that plugs a technology into a port (Postgres, OpenAI, Redis). |
| **Inbound adapter** | Something that *calls* a use case (an HTTP route, a Celery job). |
| **Outbound adapter** | Something a use case *calls* through a port (a database, a model). |
| **Composition root** | The one place that decides which adapter fills which port. |
| **Anti-corruption layer** | A translator between two contexts, so one context's model does not leak into the other. |

## The path

```mermaid
flowchart LR
    S0["0 Safety net"] --> S1["1 Feel the problem"]
    S1 --> S2["2 Find the contexts"]
    S2 --> S3["3 Skeleton and rules"]
    S3 --> S4["4 Knowledge: domain"]
    S4 --> S5["5 Knowledge: use cases and ports"]
    S5 --> S6["6 Knowledge: adapters"]
    S6 --> S7["7 Conversation: domain"]
    S7 --> S8["8 Conversation: use cases and ports"]
    S8 --> S9["9 Conversation: adapters"]
    S9 --> S10["10 Composition root"]
    S10 --> S11["11 Docker and what you gained"]
```

---

## Step 0: A safety net

### The idea

A **refactoring** changes the structure and keeps the behaviour. You need something that tells you the behaviour is the same. You already have it: `test_live.py` talks to the running app through HTTP, so it does not care how the code inside is organised.

### Type this

Run the finished part 5 app and its live test (Docker running, `OPENAI_API_KEY` set):

```bash
cd course2/fullstack-chat/my-chat            # your app from parts 1 to 5
docker compose up --build -d
cd backend && uv run python test_live.py
```

**What you should see:** `ALL LIVE TESTS PASSED`. Keep that terminal handy. You will run the same command at the end, against the new structure, **without changing the test**.

> **Ports.** Only one version can run at a time (ports 3000, 8000, 5432, 6379). Stop it with `docker compose down` before starting the other.

---

## Step 1: Feel the problem

### The problem

The layered app works, but look at where the rules live. Three real examples from `app/backend`.

**A business rule hidden in SQL.** "The first message names the chat" is encoded as a `WHERE` clause in `store.py`:

```python
await execute(
    pool,
    "UPDATE conversations SET title = %s WHERE id = %s AND title = %s",
    (content[:40], cid, DEFAULT_TITLE),
)
```

To test that rule you need a database. To change it you search SQL strings.

**A concept spelled out in many places.** The status `'queued'`, `'processing'`, `'ready'` appears as raw strings in `tasks.py` and `store.py`, and nothing says which changes are allowed.

**One function that does everything.** `chat.py` checks the rate limit (Redis), loads history (Postgres), rewrites the question (OpenAI), searches (pgvector), saves, and streams. To test any single decision you need all of Postgres, Redis and OpenAI running.

```mermaid
flowchart TB
    R["chat route"] --> RL["Redis rate limit"]
    R --> PG["Postgres SQL"]
    R --> LLM["OpenAI prompts"]
    R --> V["pgvector search"]
    R --> W["Celery tasks import the same helpers"]
```

Everything depends on everything. Replacing one technology touches many files.

### The fix, in one sentence

Put the **rules** in the middle with no technology, describe what they need as **ports**, and push every technology out to **adapters**. Do it separately for each part of the business that has its own meaning: the **contexts**.

### Check yourself

Why is "the first message names the chat" a business rule, not a database detail?

<details>
<summary>Answer</summary>

Someone could change it ("name the chat after the first *answer*") without caring how chats are stored. If a rule can change for business reasons, it belongs where business people and developers can read it, not inside a SQL string.
</details>

---

## Step 2: Find the contexts

### The idea

Listen to the language of the app. Two groups of words keep appearing:

| Conversation context | Knowledge context |
|---|---|
| conversation, message, title, history | document, category, chunk, embedding |
| question, answer, **source** | **hit**, similarity, ingest |
| rate limit | load, reload, status |

The word that sits on the border is **source** versus **hit**. To a conversation, a *source* is "a passage this answer was based on". To the knowledge base, a *hit* is "a search result with a similarity score". They look the same today, but they mean different things, so each context gets **its own class** and a translator between them.

```mermaid
flowchart LR
    subgraph C["Conversation context"]
        CD["Conversation, Message, Source"]
    end
    subgraph K["Knowledge context"]
        KD["Document, EmbeddedChunk, SearchHit"]
    end
    C -->|"asks: is it empty? search this"| G["gateway: translates SearchHit to Source"]
    G --> K
```

**Conversation is the customer, Knowledge is the supplier.** Conversation asks Knowledge questions. Knowledge knows nothing about conversations.

Rate limiting is **not** a context. It has no rules of its own beyond "N per minute", so it becomes an adapter behind a port.

### Check yourself

Why not share one `Source` class between both contexts?

<details>
<summary>Answer</summary>

If they share a class, a change for one context (say, Knowledge adds a `chunk_id`) forces a change in the other. Separate classes plus one translator keep each context free to change on its own.
</details>

---

## Step 3: The skeleton and the rules

### Type this

Create the folders in `my-chat/backend`. This is the whole structure you will fill in:

```text
backend/
  chatapp/
    shared/                       the shared kernel: tiny
    infrastructure/               settings, database plumbing, the Celery app
    knowledge/                    context 1
      domain/
      application/                use cases and ports
      adapters/
        inbound/                  HTTP routes, Celery job
        outbound/                 Postgres, pgvector, OpenAI, GitHub, Celery queue
    conversation/                 context 2 (same shape)
    container.py                  composition root
    main.py                       the web app
    worker.py                     the Celery worker entry
  tests/
```

```bash
cd course2/fullstack-chat/my-chat/backend
for d in chatapp/shared chatapp/infrastructure \
  chatapp/knowledge/{domain,application,adapters/inbound,adapters/outbound} \
  chatapp/conversation/{domain,application,adapters/inbound,adapters/outbound} tests; do
  mkdir -p $d
done
find chatapp tests -type d -exec touch {}/__init__.py \;
```

The dependency rule is one arrow:

```mermaid
flowchart LR
    A["adapters"] --> P["application: use cases and ports"] --> D["domain"]
```

**Dependencies point inward.** The domain imports nothing from outside. The application imports the domain. Adapters import the application and the domain, and the technology libraries.

### An architecture test, written first

Rules that live only in a document get broken. Turn them into a test that **reads the imports** and fails when someone cheats. Create `tests/test_architecture.py`:

```python
# needs: your backend folder (file: tests/test_architecture.py)
"""Architecture tests: the rules of the hexagon, checked by reading the imports. Pure and fast.

    uv run python -m tests.test_architecture
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "chatapp"
CONTEXTS = ("conversation", "knowledge")
# Libraries that belong in adapters, never in the domain or the application layer.
TECHNOLOGY = ("fastapi", "starlette", "pydantic", "psycopg", "psycopg_pool", "pgvector", "redis", "celery",
              "langchain", "langchain_core", "langchain_openai", "langchain_text_splitters", "openai", "httpx", "numpy")
# The one file allowed to reach from Conversation into Knowledge.
ALLOWED_CROSSING = "conversation/adapters/outbound/knowledge_gateway.py"


def imports(path: Path) -> list[str]:
    names = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def files(layer: str):
    for context in CONTEXTS:
        yield from (ROOT / context / layer).rglob("*.py")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def test_domain_and_application_use_no_technology() -> None:
    for layer in ("domain", "application"):
        for path in files(layer):
            bad = [m for m in imports(path) if m.split(".")[0] in TECHNOLOGY]
            assert not bad, f"{rel(path)} imports technology: {bad}"


def test_domain_depends_on_nothing_outward() -> None:
    for path in files("domain"):
        bad = [m for m in imports(path) if m.startswith("chatapp.") and (".adapters" in m or ".application" in m)]
        assert not bad, f"{rel(path)} (domain) imports an outer layer: {bad}"


def test_application_does_not_import_adapters() -> None:
    for path in files("application"):
        bad = [m for m in imports(path) if ".adapters" in m or m.startswith("chatapp.container")]
        assert not bad, f"{rel(path)} (application) imports an adapter: {bad}"


def test_contexts_only_meet_in_the_gateway() -> None:
    for context, other in (("conversation", "knowledge"), ("knowledge", "conversation")):
        for path in (ROOT / context).rglob("*.py"):
            if rel(path) == ALLOWED_CROSSING:
                continue
            bad = [m for m in imports(path) if m.startswith(f"chatapp.{other}")]
            assert not bad, f"{rel(path)} reaches into the {other} context: {bad}"


def test_gateway_uses_only_knowledge_use_cases() -> None:
    gateway = ROOT / ALLOWED_CROSSING
    if not gateway.exists():  # you create it in step 9
        return
    bad = [m for m in imports(gateway) if m.startswith("chatapp.knowledge") and not m.startswith("chatapp.knowledge.application")]
    assert not bad, f"the gateway should only use Knowledge's application layer: {bad}"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok  ", name)
    print("ARCHITECTURE TESTS PASSED")
```

Run it. It passes now (the folders are empty). It will keep passing only if you obey the rules as you add code:

```bash
uv run python -m tests.test_architecture
```

**What you should see:** `ARCHITECTURE TESTS PASSED`.

### Why it works

The test parses every file with Python's `ast` module and looks at the import statements. Technology libraries are banned from `domain` and `application`. Contexts may not import each other, with one exception: the gateway file. This is cheap and fast, and it needs no services.

### Try it

After step 6, add `import psycopg` to a domain file and run the test. Read the message. Then remove it.

---

## Step 4: The Knowledge domain

### The problem

What *is* a document, in this app? It has a life: queued, then processing, then ready or failed. Loading it again starts it over. Today those rules are scattered strings. Give them a home.

### Type this

First the shared kernel. It holds only what every context truly needs. Create `chatapp/shared/ids.py`:

```python
# needs: your backend folder (file: chatapp/shared/ids.py)
"""The shared kernel: the few things every context needs. Keep it tiny."""
import uuid


def new_id() -> str:
    return uuid.uuid4().hex[:8]
```

The catalog says what the knowledge base is made of: the ten OWASP categories. This is domain knowledge, so it lives in the domain. Create `chatapp/knowledge/domain/catalog.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/domain/catalog.py)
"""What the knowledge base is made of: the ten OWASP Top 10:2025 categories.
The text is published by OWASP under CC BY-SA 4.0: https://github.com/OWASP/Top10"""
from dataclasses import dataclass

PAGE = "https://owasp.org/Top10/2025/{slug}/"


@dataclass(frozen=True)
class CatalogEntry:
    key: str    # "A05:2025"
    name: str   # "Injection"
    slug: str   # the page name, "A05_2025-Injection"

    @property
    def title(self) -> str:
        return f"{self.key} {self.name}"

    @property
    def page_url(self) -> str:
        return PAGE.format(slug=self.slug)


CATALOG = (
    CatalogEntry("A01:2025", "Broken Access Control", "A01_2025-Broken_Access_Control"),
    CatalogEntry("A02:2025", "Security Misconfiguration", "A02_2025-Security_Misconfiguration"),
    CatalogEntry("A03:2025", "Software Supply Chain Failures", "A03_2025-Software_Supply_Chain_Failures"),
    CatalogEntry("A04:2025", "Cryptographic Failures", "A04_2025-Cryptographic_Failures"),
    CatalogEntry("A05:2025", "Injection", "A05_2025-Injection"),
    CatalogEntry("A06:2025", "Insecure Design", "A06_2025-Insecure_Design"),
    CatalogEntry("A07:2025", "Authentication Failures", "A07_2025-Authentication_Failures"),
    CatalogEntry("A08:2025", "Software or Data Integrity Failures", "A08_2025-Software_or_Data_Integrity_Failures"),
    CatalogEntry("A09:2025", "Security Logging and Alerting Failures", "A09_2025-Security_Logging_and_Alerting_Failures"),
    CatalogEntry("A10:2025", "Mishandling of Exceptional Conditions", "A10_2025-Mishandling_of_Exceptional_Conditions"),
)


def entry_for(key: str) -> CatalogEntry:
    for entry in CATALOG:
        if entry.key == key:
            return entry
    raise KeyError(f"{key} is not in the catalog")
```

Now the entity with its life cycle, and two value objects. Create `chatapp/knowledge/domain/document.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/domain/document.py)
"""The Document entity and the rules about its life. No database, no web, no AI in here."""
from dataclasses import dataclass
from enum import StrEnum

from chatapp.knowledge.domain.catalog import CatalogEntry

MAX_ERROR_LENGTH = 200


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Document:
    key: str
    title: str
    url: str
    status: DocumentStatus = DocumentStatus.QUEUED
    chunks: int = 0
    error: str = ""
    id: int | None = None  # the database gives it one when it is first saved

    @classmethod
    def queued(cls, entry: CatalogEntry) -> "Document":
        return cls(key=entry.key, title=entry.title, url=entry.page_url)

    # The life of a document: queued -> processing -> ready or failed. Loading again starts over.
    def start(self) -> None:
        self.status = DocumentStatus.PROCESSING

    def finish(self, chunks: int) -> None:
        self.status, self.chunks, self.error = DocumentStatus.READY, chunks, ""

    def fail(self, reason: str) -> None:
        self.status, self.error = DocumentStatus.FAILED, reason[:MAX_ERROR_LENGTH]

    def requeue(self) -> None:
        self.status, self.error = DocumentStatus.QUEUED, ""

    def embedding_text(self, chunk: str) -> str:
        # A chunk like "Use parameterized queries" does not say which category it belongs to.
        # Putting the title in front helps its vector land near the right topic.
        return f"{self.title}\n\n{chunk}"


@dataclass(frozen=True)
class EmbeddedChunk:
    text: str
    vector: list[float]


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    text: str
    score: float  # cosine similarity: 1 means the same direction, near 0 means unrelated
```

Read it: there is no SQL, no HTTP, no OpenAI. `Document.queued(entry)`, `start()`, `finish(n)`, `fail(reason)` and `requeue()` are the vocabulary the rest of the app will use. `embedding_text(chunk)` holds the rule "put the title in front before embedding", which used to be a loose function.

### Test the domain, with no services and no fakes

The domain is plain Python, so its tests are plain too. Create `tests/test_domain.py` with the Knowledge tests (you will extend it in step 7):

```python
# needs: your backend folder (file: tests/test_domain.py)
"""Pure domain tests. The domain has no database, web or AI code, so these need no services and no fakes.

    uv run python -m tests.test_domain
"""
from chatapp.knowledge.domain.catalog import CATALOG, entry_for
from chatapp.knowledge.domain.document import Document, DocumentStatus


def test_document_life_cycle() -> None:
    doc = Document.queued(entry_for("A05:2025"))
    assert doc.status is DocumentStatus.QUEUED and doc.title == "A05:2025 Injection"
    assert doc.url == "https://owasp.org/Top10/2025/A05_2025-Injection/"
    doc.start()
    assert doc.status is DocumentStatus.PROCESSING
    doc.finish(16)
    assert (doc.status, doc.chunks, doc.error) == (DocumentStatus.READY, 16, "")
    doc.fail("x" * 500)
    assert doc.status is DocumentStatus.FAILED and len(doc.error) == 200
    doc.requeue()
    assert (doc.status, doc.error) == (DocumentStatus.QUEUED, "")


def test_embedding_text_puts_the_title_first() -> None:
    doc = Document.queued(entry_for("A05:2025"))
    assert doc.embedding_text("Use parameterized queries.") == "A05:2025 Injection\n\nUse parameterized queries."


def test_catalog_is_the_ten_owasp_categories() -> None:
    assert len(CATALOG) == 10
    assert [e.key for e in CATALOG] == [f"A{n:02d}:2025" for n in range(1, 11)]
    assert len({e.slug for e in CATALOG}) == 10


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok  ", name)
    print("DOMAIN TESTS PASSED")
```

```bash
uv run python -m tests.test_domain
```

**What you should see:** `DOMAIN TESTS PASSED`. They run in milliseconds. You never needed a database to check "a failed document keeps only 200 characters of its error".

### Check yourself

`Document.fail(reason)` cuts the reason to 200 characters. Why is that in the domain and not in the database adapter?

<details>
<summary>Answer</summary>

It is a rule about what a Document *is* (an error message is short), not about how it is stored. If we swapped Postgres for another store, the rule would have to stay the same.
</details>

---

## Step 5: Knowledge use cases and ports

### The problem

The domain says what a document is. Something must say what you can *do*: load the knowledge base, ingest one document, search, list. And those actions need things from outside: a place to keep documents, an embedder, a queue. The domain must not know those technologies.

### The fix: use cases, with ports for what they need

A **port** is an interface named for the *need*. `Embedder` and `JobQueue`, not `OpenAIClient` and `CeleryApp`.

```mermaid
flowchart LR
    UC["Use cases: Load, Ingest, Search, List"] --> P1["DocumentRepository"]
    UC --> P2["ChunkStore"]
    UC --> P3["Embedder"]
    UC --> P4["DocumentSource"]
    UC --> P5["TextSplitter"]
    UC --> P6["JobQueue"]
```

### Type this

The ports. They are Python `Protocol` classes: any class with these methods fits, with no inheritance needed. Create `chatapp/knowledge/application/ports.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/application/ports.py)
"""The ports of the Knowledge context: what its use cases need from the outside world.
Each one is named for the need, not for a tool. Adapters implement them."""
from collections.abc import Sequence
from typing import Protocol

from chatapp.knowledge.domain.document import Document, EmbeddedChunk, SearchHit


class DocumentRepository(Protocol):
    async def upsert(self, document: Document) -> Document: ...  # insert, or reset the same key; returns it with an id
    async def get(self, document_id: int) -> Document | None: ...
    async def save(self, document: Document) -> None: ...
    async def list_all(self) -> list[Document]: ...


class ChunkStore(Protocol):
    async def replace(self, document_id: int, chunks: Sequence[EmbeddedChunk]) -> None: ...
    async def search(self, vector: list[float], k: int) -> list[SearchHit]: ...
    async def count(self) -> int: ...


class Embedder(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...


class DocumentSource(Protocol):
    async def fetch(self, key: str) -> str: ...  # the text of one catalog entry


class TextSplitter(Protocol):
    def split(self, text: str) -> list[str]: ...


class JobQueue(Protocol):
    def enqueue_ingest(self, document_id: int) -> None: ...  # run IngestDocument later, somewhere else
```

The use cases. Create `chatapp/knowledge/application/use_cases.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/application/use_cases.py)
"""The use cases of the Knowledge context. They orchestrate domain objects through ports."""
from chatapp.knowledge.application.ports import ChunkStore, DocumentRepository, DocumentSource, Embedder, JobQueue, TextSplitter
from chatapp.knowledge.domain.catalog import CATALOG
from chatapp.knowledge.domain.document import Document, EmbeddedChunk, SearchHit


class LoadKnowledgeBase:
    """Queue every catalog entry for ingestion. Calling it twice resets the documents, never duplicates them."""

    def __init__(self, documents: DocumentRepository, jobs: JobQueue) -> None:
        self.documents, self.jobs = documents, jobs

    async def execute(self) -> int:
        for entry in CATALOG:
            document = await self.documents.upsert(Document.queued(entry))
            self.jobs.enqueue_ingest(document.id)
        return len(CATALOG)


class IngestDocument:
    """Download, split, embed and store one document. Runs in the worker."""

    def __init__(self, documents: DocumentRepository, chunks: ChunkStore, source: DocumentSource,
                 splitter: TextSplitter, embedder: Embedder) -> None:
        self.documents, self.chunks, self.source = documents, chunks, source
        self.splitter, self.embedder = splitter, embedder

    async def execute(self, document_id: int) -> int:
        document = await self.documents.get(document_id)
        if document is None:
            raise LookupError(f"document {document_id} does not exist")
        document.start()
        await self.documents.save(document)
        try:
            parts = self.splitter.split(await self.source.fetch(document.key))
            vectors = await self.embedder.embed_documents([document.embedding_text(p) for p in parts])
            await self.chunks.replace(document.id, [EmbeddedChunk(p, v) for p, v in zip(parts, vectors)])
            document.finish(len(parts))
            return len(parts)
        except Exception as e:  # show the reason in the page instead of failing silently
            document.fail(str(e))
            raise
        finally:
            await self.documents.save(document)


class ListKnowledge:
    def __init__(self, documents: DocumentRepository) -> None:
        self.documents = documents

    async def execute(self) -> list[Document]:
        return await self.documents.list_all()


class SearchKnowledge:
    def __init__(self, chunks: ChunkStore, embedder: Embedder) -> None:
        self.chunks, self.embedder = chunks, embedder

    async def execute(self, question: str, k: int) -> list[SearchHit]:
        return await self.chunks.search(await self.embedder.embed_query(question), k)


class CountKnowledge:
    def __init__(self, chunks: ChunkStore) -> None:
        self.chunks = chunks

    async def execute(self) -> int:
        return await self.chunks.count()
```

Read `IngestDocument`. It is the old Celery task, now free of technology: get the document, `start()`, fetch the text, split, embed, store, `finish()`. If anything fails, `fail()` and re-raise. The `finally` always saves the new status. Nothing here knows about Postgres, GitHub or OpenAI.

Run `uv run python -m tests.test_architecture`: still passing, because `application` imports only the domain and its own ports.

### Why it works

The use case depends on **abstractions it owns** (the ports), not on tools. That reverses the usual dependency: instead of the business logic importing the database, the database adapter imports the port. This is the "dependency inversion" you hear about.

### Check yourself

Why is `JobQueue.enqueue_ingest` a plain method, not `async`?

<details>
<summary>Answer</summary>

Putting a job on the queue is a quick, fire-and-forget call. The port describes what the use case needs, and it needs nothing awaitable here. The adapter is free to do the work however it likes.
</details>

---

## Step 6: Knowledge adapters

### The idea

Now the technology. Each adapter implements one port with one tool. They are all small.

```mermaid
flowchart TB
    subgraph out["Outbound adapters: the use case calls them through ports"]
        A1["PostgresDocumentRepository"]
        A2["PgVectorChunkStore"]
        A3["OpenAIEmbedder"]
        A4["GithubOwaspSource"]
        A5["MarkdownSplitter"]
        A6["CeleryJobQueue"]
    end
    subgraph inb["Inbound adapters: they call the use cases"]
        B1["HTTP routes"]
        B2["Celery job"]
    end
```

### Type this

First the shared infrastructure. Settings, database plumbing and the Celery app. They are not a context, they are plumbing every adapter shares. Copy your `schema.sql` from part 3 into `chatapp/infrastructure/schema.sql` (it does not change). Then create `chatapp/infrastructure/settings.py`:

```python
# needs: your backend folder (file: chatapp/infrastructure/settings.py)
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chat:chat@localhost:5432/chat")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # 1536 dimensions, matches schema.sql
FRONTEND_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
HISTORY_LIMIT = 10  # last N messages sent to the model
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
```

`chatapp/infrastructure/db.py`:

```python
# needs: your backend folder (file: chatapp/infrastructure/db.py)
"""Postgres plumbing shared by the outbound adapters of every context."""
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from chatapp.infrastructure import settings

SCHEMA = Path(__file__).with_name("schema.sql")


def init_schema() -> None:
    # Safe to run on every start: every statement says IF NOT EXISTS.
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        conn.execute(SCHEMA.read_text())


async def _configure(conn) -> None:
    await register_vector_async(conn)  # lets us pass numpy arrays as vectors


def make_pool() -> AsyncConnectionPool:
    return AsyncConnectionPool(
        settings.DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        configure=_configure,
        kwargs={"row_factory": dict_row, "autocommit": True},
    )


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

`chatapp/infrastructure/celery_app.py`:

```python
# needs: your backend folder (file: chatapp/infrastructure/celery_app.py)
"""The Celery app. Both the queue adapter (sending jobs) and the worker (running them) use it."""
from celery import Celery

from chatapp.infrastructure import settings

celery_app = Celery("chat", broker=settings.REDIS_URL)  # status lives in Postgres, so no result backend
```

**Documents in Postgres.** `chatapp/knowledge/adapters/outbound/postgres_documents.py`. All the SQL for documents is now in one place, and it converts rows to `Document` objects:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/outbound/postgres_documents.py)
from psycopg_pool import AsyncConnectionPool

from chatapp.infrastructure import db
from chatapp.knowledge.domain.document import Document, DocumentStatus


def _to_document(row: dict) -> Document:
    return Document(id=row["id"], key=row["key"], title=row["title"], url=row["url"],
                    status=DocumentStatus(row["status"]), chunks=row["chunks"], error=row["error"])


COLUMNS = "id, key, title, url, status, chunks, error"


class PostgresDocumentRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def upsert(self, document: Document) -> Document:
        row = await db.one(
            self.pool,
            "INSERT INTO documents (key, title, url, status) VALUES (%s, %s, %s, 'queued') "
            f"ON CONFLICT (key) DO UPDATE SET status = 'queued', error = '', updated_at = now() RETURNING {COLUMNS}",
            (document.key, document.title, document.url),
        )
        return _to_document(row)

    async def get(self, document_id: int) -> Document | None:
        row = await db.one(self.pool, f"SELECT {COLUMNS} FROM documents WHERE id = %s", (document_id,))
        return _to_document(row) if row else None

    async def save(self, document: Document) -> None:
        await db.execute(
            self.pool,
            "UPDATE documents SET status = %s, chunks = %s, error = %s, updated_at = now() WHERE id = %s",
            (document.status.value, document.chunks, document.error, document.id),
        )

    async def list_all(self) -> list[Document]:
        return [_to_document(r) for r in await db.many(self.pool, f"SELECT {COLUMNS} FROM documents ORDER BY key")]
```

**Chunks in pgvector.** `chatapp/knowledge/adapters/outbound/pgvector_chunks.py`. The vector search SQL lives here. `replace` runs in a transaction, which is safer than before:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/outbound/pgvector_chunks.py)
from collections.abc import Sequence

import numpy as np
from psycopg_pool import AsyncConnectionPool

from chatapp.infrastructure import db
from chatapp.knowledge.domain.document import EmbeddedChunk, SearchHit


class PgVectorChunkStore:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def replace(self, document_id: int, chunks: Sequence[EmbeddedChunk]) -> None:
        async with self.pool.connection() as conn, conn.transaction():  # all or nothing
            await conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))  # reloading replaces, never duplicates
            for position, chunk in enumerate(chunks):
                await conn.execute(
                    "INSERT INTO chunks (document_id, position, content, embedding) VALUES (%s, %s, %s, %s)",
                    (document_id, position, chunk.text, np.array(chunk.vector)),
                )

    async def search(self, vector: list[float], k: int) -> list[SearchHit]:
        # <=> is pgvector's cosine DISTANCE (0 = same direction). 1 - distance = similarity.
        rows = await db.many(
            self.pool,
            "SELECT d.title, d.url, c.content AS text, 1 - (c.embedding <=> %s) AS score "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "ORDER BY c.embedding <=> %s LIMIT %s",
            (np.array(vector), np.array(vector), k),
        )
        return [SearchHit(r["title"], r["url"], r["text"], round(float(r["score"]), 4)) for r in rows]

    async def count(self) -> int:
        return (await db.one(self.pool, "SELECT count(*) AS n FROM chunks"))["n"]
```

**The embedder, the text source, the splitter and the queue.** Four tiny adapters. `chatapp/knowledge/adapters/outbound/openai_embedder.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/outbound/openai_embedder.py)
from langchain_openai import OpenAIEmbeddings

from chatapp.infrastructure import settings


class OpenAIEmbedder:
    def __init__(self) -> None:
        self.model = OpenAIEmbeddings(model=settings.EMBED_MODEL)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self.model.aembed_documents(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self.model.aembed_query(text)
```

`chatapp/knowledge/adapters/outbound/github_source.py`. Cleaning the OWASP Markdown is about *this source's format*, so it belongs here, not in the domain:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/outbound/github_source.py)
"""Fetches the OWASP pages from GitHub and cleans the Markdown."""
import re

import httpx

from chatapp.knowledge.domain.catalog import entry_for

RAW = "https://raw.githubusercontent.com/OWASP/Top10/master/2025/docs/en/{slug}.md"


def clean(md: str) -> str:
    md = re.sub(r"<table>.*?</table>", "", md, flags=re.S)  # score tables are numbers, not prose
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?", "", md)  # icons and images
    md = re.sub(r"[ \t]+\n", "\n", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


class GithubOwaspSource:
    async def fetch(self, key: str) -> str:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            res = await client.get(RAW.format(slug=entry_for(key).slug))  # the domain knows the page name
        res.raise_for_status()
        return clean(res.text)
```

`chatapp/knowledge/adapters/outbound/markdown_splitter.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/outbound/markdown_splitter.py)
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


class MarkdownSplitter:
    def __init__(self) -> None:
        # Markdown-aware: prefers to cut at headings and paragraphs, not mid-sentence.
        self.splitter = RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=1000, chunk_overlap=150)

    def split(self, text: str) -> list[str]:
        return [d.page_content for d in self.splitter.create_documents([text])]
```

`chatapp/knowledge/adapters/outbound/celery_queue.py`. It sends a job **by name**, so the use case side never imports the worker code:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/outbound/celery_queue.py)
from chatapp.infrastructure.celery_app import celery_app


class CeleryJobQueue:
    def enqueue_ingest(self, document_id: int) -> None:
        # Sends a message by task NAME, so this adapter never imports the worker code.
        celery_app.send_task("knowledge.ingest_document", args=[document_id])
```

**Inbound adapters.** An HTTP route and a Celery job are the same kind of thing: both receive a request from outside and call a use case. `chatapp/knowledge/adapters/inbound/http.py`:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/inbound/http.py)
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/knowledge")


def container(request: Request):
    return request.app.state.container


@router.get("")
async def documents(request: Request):
    docs = await container(request).knowledge.list_knowledge.execute()
    return [
        {"id": d.id, "key": d.key, "title": d.title, "status": d.status.value, "chunks": d.chunks, "error": d.error}
        for d in docs
    ]


@router.post("/load")
async def load(request: Request):
    return {"queued": await container(request).knowledge.load_knowledge_base.execute()}
```

`chatapp/knowledge/adapters/inbound/celery_tasks.py`. The worker is its own process, so it builds its own container (its own connections) for each job:

```python
# needs: your backend folder (file: chatapp/knowledge/adapters/inbound/celery_tasks.py)
"""Inbound adapter: a Celery job that calls a use case, just like an HTTP route does."""
import asyncio

from chatapp.container import build_container
from chatapp.infrastructure.celery_app import celery_app


@celery_app.task(name="knowledge.ingest_document")
def ingest_document(document_id: int) -> int:
    return asyncio.run(_run(document_id))


async def _run(document_id: int) -> int:
    # The worker is its own process, so it builds its own container (its own connections).
    async with build_container() as container:
        return await container.knowledge.ingest_document.execute(document_id)
```

(`build_container` comes in step 10. Do not run this yet.)

### Why it works

Each adapter has one reason to change. A new embedding provider means writing one new file that fits `Embedder`. The use case and the domain do not change.

### Try it

Run the architecture test. Then ask yourself: if you swapped OpenAI for another embedding provider, how many files would change?

<details>
<summary>Answer</summary>

Two: the new adapter file, and one line in the composition root (step 10) that says which adapter to use.
</details>

---

## Step 7: The Conversation domain

### The problem

Same exercise for the other context. What is a conversation? A thing with an id and a title. A message has a role, text and the sources it was based on. And the rules: the first message names the chat, and a blank question is invalid.

### Type this

`chatapp/conversation/domain/message.py`. Notice `Source` is Conversation's *own* class, not Knowledge's `SearchHit`:

```python
# needs: your backend folder (file: chatapp/conversation/domain/message.py)
from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Source:
    """A passage an answer was based on. Conversation's own word for it: it does not import Knowledge's."""
    title: str
    url: str
    text: str
    score: float


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    sources: tuple[Source, ...] = ()
```

`chatapp/conversation/domain/conversation.py`. The rule that was a SQL `WHERE` clause is now a readable method:

```python
# needs: your backend folder (file: chatapp/conversation/domain/conversation.py)
"""The Conversation entity and its rules. No database, no web, no AI in here."""
from dataclasses import dataclass

from chatapp.shared.ids import new_id

DEFAULT_TITLE = "New chat"
TITLE_LENGTH = 40


class InvalidQuestion(ValueError):
    pass


def clean_question(text: str) -> str:
    text = text.strip()
    if not text:
        raise InvalidQuestion("The message is empty.")
    return text


@dataclass
class Conversation:
    id: str
    title: str = DEFAULT_TITLE

    @classmethod
    def start(cls) -> "Conversation":
        return cls(id=new_id())

    def name_from(self, first_message: str) -> bool:
        """The first message names the chat. Returns True when the title changed."""
        if self.title != DEFAULT_TITLE:
            return False
        self.title = first_message[:TITLE_LENGTH]
        return True
```

Read `name_from`: "if the title is still the default, use the first message, and tell me whether it changed". That is the business rule, in plain Python.

Add the Conversation rules to the domain tests. Replace `tests/test_domain.py` with this fuller version, which keeps the Knowledge tests and adds two more:

```python
# needs: your backend folder (file: tests/test_domain.py)
"""Pure domain tests. The domain has no database, web or AI code, so these need no services and no fakes.

    uv run python -m tests.test_domain
"""
from chatapp.conversation.domain.conversation import DEFAULT_TITLE, TITLE_LENGTH, Conversation, InvalidQuestion, clean_question
from chatapp.knowledge.domain.catalog import CATALOG, entry_for
from chatapp.knowledge.domain.document import Document, DocumentStatus


def test_first_message_names_the_conversation() -> None:
    c = Conversation.start()
    assert c.title == DEFAULT_TITLE
    first = "What is SQL injection and how do I prevent it?"
    assert c.name_from(first) is True
    assert c.title == first[:TITLE_LENGTH] and len(c.title) == TITLE_LENGTH
    assert c.name_from("A second message") is False  # later messages do not rename it
    assert c.title.startswith("What is SQL")


def test_question_must_not_be_blank() -> None:
    assert clean_question("  hello  ") == "hello"
    for blank in ("", "   ", "\n"):
        try:
            clean_question(blank)
        except InvalidQuestion:
            continue
        raise AssertionError(f"{blank!r} should be rejected")


def test_document_life_cycle() -> None:
    doc = Document.queued(entry_for("A05:2025"))
    assert doc.status is DocumentStatus.QUEUED and doc.title == "A05:2025 Injection"
    assert doc.url == "https://owasp.org/Top10/2025/A05_2025-Injection/"
    doc.start()
    assert doc.status is DocumentStatus.PROCESSING
    doc.finish(16)
    assert (doc.status, doc.chunks, doc.error) == (DocumentStatus.READY, 16, "")
    doc.fail("x" * 500)
    assert doc.status is DocumentStatus.FAILED and len(doc.error) == 200
    doc.requeue()
    assert (doc.status, doc.error) == (DocumentStatus.QUEUED, "")


def test_embedding_text_puts_the_title_first() -> None:
    doc = Document.queued(entry_for("A05:2025"))
    assert doc.embedding_text("Use parameterized queries.") == "A05:2025 Injection\n\nUse parameterized queries."


def test_catalog_is_the_ten_owasp_categories() -> None:
    assert len(CATALOG) == 10
    assert [e.key for e in CATALOG] == [f"A{n:02d}:2025" for n in range(1, 11)]
    assert len({e.slug for e in CATALOG}) == 10


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok  ", name)
    print("DOMAIN TESTS PASSED")
```

Run them:

```bash
uv run python -m tests.test_domain
uv run python -m tests.test_architecture
```

**What you should see:** both pass. The two contexts' domains do not import each other.

### Check yourself

Why does `Conversation.name_from` return a boolean?

<details>
<summary>Answer</summary>

The use case needs to know whether to save the new title. Returning "did it change?" lets the use case stay simple (`if conversation.name_from(...): save`) while the rule stays in the domain.
</details>

---

## Step 8: Conversation use cases and ports

### The problem

"Send a message" is the heart of the app: check the rate limit, check the chat exists, check there is knowledge, rewrite the question, search, save, then stream an answer. It needs a rate limiter, a repository, a model and *knowledge*, but it must not know any of those technologies.

### The fix

```mermaid
flowchart LR
    SM["SendMessage"] --> P1["RateLimiter"]
    SM --> P2["ConversationRepository"]
    SM --> P3["KnowledgeSearch"]
    SM --> P4["AnswerGenerator"]
```

`KnowledgeSearch` is the port that expresses what Conversation needs from the *other context*, in Conversation's own words: "is it empty?" and "search this, give me sources".

### Type this

The errors this context can raise. The HTTP layer will turn them into status codes. The domain never says "404". `chatapp/conversation/application/errors.py`:

```python
# needs: your backend folder (file: chatapp/conversation/application/errors.py)
class ConversationError(Exception):
    """Base class for the things that can go wrong in the Conversation use cases."""


class ConversationNotFound(ConversationError):
    pass


class RateLimitExceeded(ConversationError):
    pass


class KnowledgeBaseEmpty(ConversationError):
    pass
```

The events a streamed answer is made of. `chatapp/conversation/application/events.py`:

```python
# needs: your backend folder (file: chatapp/conversation/application/events.py)
"""What a streamed answer is made of. The inbound adapter turns these into server-sent events."""
from dataclasses import dataclass

from chatapp.conversation.domain.message import Source


@dataclass(frozen=True)
class TokenGenerated:
    text: str


@dataclass(frozen=True)
class SourcesFound:
    sources: tuple[Source, ...]


@dataclass(frozen=True)
class AnswerFailed:
    message: str


@dataclass(frozen=True)
class AnswerFinished:
    pass


ChatEvent = TokenGenerated | SourcesFound | AnswerFailed | AnswerFinished
```

The ports. `chatapp/conversation/application/ports.py`:

```python
# needs: your backend folder (file: chatapp/conversation/application/ports.py)
"""The ports of the Conversation context: what its use cases need from the outside world."""
from collections.abc import AsyncIterator
from typing import Protocol

from chatapp.conversation.domain.conversation import Conversation
from chatapp.conversation.domain.message import Message, Source


class ConversationRepository(Protocol):
    async def add(self, conversation: Conversation) -> None: ...
    async def get(self, conversation_id: str) -> Conversation | None: ...
    async def list_all(self) -> list[Conversation]: ...
    async def rename(self, conversation: Conversation) -> None: ...
    async def delete(self, conversation_id: str) -> None: ...
    async def append(self, conversation_id: str, message: Message) -> None: ...
    async def messages(self, conversation_id: str, limit: int | None = None) -> list[Message]: ...


class AnswerGenerator(Protocol):
    async def standalone_question(self, history: list[Message], question: str) -> str: ...
    def stream(self, history: list[Message], question: str, sources: list[Source]) -> AsyncIterator[str]: ...


class KnowledgeSearch(Protocol):
    """What Conversation needs from the Knowledge context, in Conversation's own words."""
    async def is_empty(self) -> bool: ...
    async def search(self, question: str, k: int) -> list[Source]: ...


class RateLimiter(Protocol):
    async def is_limited(self, client_id: str) -> bool: ...  # counts this call, then says whether it is over the limit
```

The use cases. `chatapp/conversation/application/use_cases.py`:

```python
# needs: your backend folder (file: chatapp/conversation/application/use_cases.py)
"""The use cases of the Conversation context."""
from collections.abc import AsyncIterator

from chatapp.conversation.application.errors import ConversationNotFound, KnowledgeBaseEmpty, RateLimitExceeded
from chatapp.conversation.application.events import AnswerFailed, AnswerFinished, ChatEvent, SourcesFound, TokenGenerated
from chatapp.conversation.application.ports import AnswerGenerator, ConversationRepository, KnowledgeSearch, RateLimiter
from chatapp.conversation.domain.conversation import Conversation, clean_question
from chatapp.conversation.domain.message import Message, Role, Source


class StartConversation:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self) -> Conversation:
        conversation = Conversation.start()
        await self.conversations.add(conversation)
        return conversation


class ListConversations:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self) -> list[Conversation]:
        return await self.conversations.list_all()


class GetMessages:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self, conversation_id: str) -> list[Message]:
        if await self.conversations.get(conversation_id) is None:
            raise ConversationNotFound(conversation_id)
        return await self.conversations.messages(conversation_id)


class DeleteConversation:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self, conversation_id: str) -> None:
        await self.conversations.delete(conversation_id)


class AnswerStream:
    """A question that passed every check. Iterating `events()` produces the answer."""

    def __init__(self, conversations: ConversationRepository, answers: AnswerGenerator, conversation_id: str,
                 history: list[Message], question: str, sources: list[Source]) -> None:
        self.conversations, self.answers = conversations, answers
        self.conversation_id, self.history, self.question, self.sources = conversation_id, history, question, sources

    async def events(self) -> AsyncIterator[ChatEvent]:
        parts: list[str] = []
        try:
            async for token in self.answers.stream(self.history, self.question, self.sources):
                parts.append(token)
                yield TokenGenerated(token)
        except Exception as e:  # tell the page, instead of cutting the stream
            yield AnswerFailed(str(e)[:200])
            return
        await self.conversations.append(self.conversation_id, Message(Role.ASSISTANT, "".join(parts), tuple(self.sources)))
        yield SourcesFound(tuple(self.sources))
        yield AnswerFinished()


class SendMessage:
    def __init__(self, conversations: ConversationRepository, answers: AnswerGenerator, knowledge: KnowledgeSearch,
                 limiter: RateLimiter, history_window: int) -> None:
        self.conversations, self.answers, self.knowledge = conversations, answers, knowledge
        self.limiter, self.history_window = limiter, history_window

    async def execute(self, conversation_id: str, text: str, k: int, client_id: str) -> AnswerStream:
        # Every check happens here, before any streaming starts, so the page gets a real error code.
        if await self.limiter.is_limited(client_id):
            raise RateLimitExceeded(client_id)
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFound(conversation_id)
        if await self.knowledge.is_empty():
            raise KnowledgeBaseEmpty()
        question = clean_question(text)

        history = await self.conversations.messages(conversation_id, limit=self.history_window)
        search_text = await self.answers.standalone_question(history, question)
        sources = await self.knowledge.search(search_text, k)

        await self.conversations.append(conversation_id, Message(Role.USER, question))
        if conversation.name_from(question):
            await self.conversations.rename(conversation)
        return AnswerStream(self.conversations, self.answers, conversation_id, history, question, sources)
```

Two things to notice in `SendMessage.execute`:

1. **Every check happens before any streaming starts.** If the use case itself were the stream, an error would only appear on the first iteration, after the HTTP status `200` was already sent. So `execute` is a normal `async` function that does all the checks and returns an `AnswerStream`. Only then does the adapter start streaming.
2. **It never says "Postgres" or "OpenAI" or "Redis".** Read the constructor: four ports and a number.

### Check yourself

What would you change to add a rule "free users get 5 messages a day"?

<details>
<summary>Answer</summary>

Only the `RateLimiter` implementation (or a second port). `SendMessage` already asks `is_limited(client_id)`. No route, no SQL and no prompt changes.
</details>

---

## Step 9: Conversation adapters

### Type this

**Conversations in Postgres.** `chatapp/conversation/adapters/outbound/postgres_conversations.py`:

```python
# needs: your backend folder (file: chatapp/conversation/adapters/outbound/postgres_conversations.py)
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from chatapp.conversation.domain.conversation import Conversation
from chatapp.conversation.domain.message import Message, Role, Source
from chatapp.infrastructure import db


class PostgresConversationRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def add(self, conversation: Conversation) -> None:
        await db.execute(self.pool, "INSERT INTO conversations (id, title) VALUES (%s, %s)", (conversation.id, conversation.title))

    async def get(self, conversation_id: str) -> Conversation | None:
        row = await db.one(self.pool, "SELECT id, title FROM conversations WHERE id = %s", (conversation_id,))
        return Conversation(**row) if row else None

    async def list_all(self) -> list[Conversation]:
        rows = await db.many(self.pool, "SELECT id, title FROM conversations ORDER BY created_at DESC")
        return [Conversation(**r) for r in rows]

    async def rename(self, conversation: Conversation) -> None:
        await db.execute(self.pool, "UPDATE conversations SET title = %s WHERE id = %s", (conversation.title, conversation.id))

    async def delete(self, conversation_id: str) -> None:
        await db.execute(self.pool, "DELETE FROM conversations WHERE id = %s", (conversation_id,))  # messages go too (ON DELETE CASCADE)

    async def append(self, conversation_id: str, message: Message) -> None:
        sources = [{"title": s.title, "url": s.url, "text": s.text, "score": s.score} for s in message.sources]
        await db.execute(
            self.pool,
            "INSERT INTO messages (conversation_id, role, content, sources) VALUES (%s, %s, %s, %s)",
            (conversation_id, message.role.value, message.content, Jsonb(sources)),
        )

    async def messages(self, conversation_id: str, limit: int | None = None) -> list[Message]:
        # Newest N, then put them back in time order.
        rows = await db.many(
            self.pool,
            "SELECT role, content, sources FROM ("
            "  SELECT id, role, content, sources FROM messages WHERE conversation_id = %s ORDER BY id DESC LIMIT %s"
            ") recent ORDER BY id",
            (conversation_id, limit),
        )
        return [Message(Role(r["role"]), r["content"], tuple(Source(**s) for s in r["sources"])) for r in rows]
```

**The model.** The prompts moved here: they are about how *this* model is talked to, not about the business. `chatapp/conversation/adapters/outbound/openai_answers.py`:

```python
# needs: your backend folder (file: chatapp/conversation/adapters/outbound/openai_answers.py)
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from chatapp.conversation.domain.message import Message, Role, Source
from chatapp.infrastructure import settings

SYSTEM = (
    "You are a security assistant that answers questions about the OWASP Top 10:2025. "
    "Use only the context below. Name the category you rely on, like [A05:2025], in your answer. "
    "If the context does not contain the answer, say you don't know and suggest which OWASP "
    "category might be related. Be concise and practical.\n\nContext:\n{context}"
)
REWRITE = (
    "Rewrite the user's last question so it makes sense on its own, using the chat history. "
    "Return only the question."
)


def _llm(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(model=settings.CHAT_MODEL, **kwargs)


def _to_langchain(history: list[Message]):
    return [HumanMessage(m.content) if m.role is Role.USER else AIMessage(m.content) for m in history]


class OpenAIAnswerGenerator:
    async def standalone_question(self, history: list[Message], question: str) -> str:
        # "How do I prevent it?" cannot be searched. "How do I prevent SQL injection?" can.
        if not history:
            return question
        messages = [SystemMessage(REWRITE), *_to_langchain(history), HumanMessage(question)]
        return (await _llm(temperature=0, max_tokens=100).ainvoke(messages)).content.strip()

    async def stream(self, history: list[Message], question: str, sources: list[Source]) -> AsyncIterator[str]:
        context = "\n\n".join(f"[{s.title}]\n{s.text}" for s in sources)
        messages = [SystemMessage(SYSTEM.format(context=context)), *_to_langchain(history), HumanMessage(question)]
        async for chunk in _llm(temperature=0.2, max_tokens=600).astream(messages):
            if chunk.content:
                yield chunk.content
```

**Redis rate limiting.** `chatapp/conversation/adapters/outbound/redis_rate_limiter.py`:

```python
# needs: your backend folder (file: chatapp/conversation/adapters/outbound/redis_rate_limiter.py)
import time

from redis.asyncio import Redis


class RedisRateLimiter:
    def __init__(self, redis: Redis, limit_per_minute: int) -> None:
        self.redis, self.limit = redis, limit_per_minute

    async def is_limited(self, client_id: str) -> bool:
        key = f"rate:{client_id}:{int(time.time() // 60)}"  # one counter per client per minute
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)  # the counter deletes itself, no cleanup code needed
        return count > self.limit
```

**The gateway to Knowledge.** This is the one file where the two contexts meet. It calls Knowledge's *use cases* and translates its `SearchHit` into Conversation's `Source`. Create `chatapp/conversation/adapters/outbound/knowledge_gateway.py`:

```python
# needs: your backend folder (file: chatapp/conversation/adapters/outbound/knowledge_gateway.py)
"""The ONLY place the Conversation context touches the Knowledge context.
It is an anti-corruption layer: it calls Knowledge's use cases and translates the results into Conversation's own types."""
from chatapp.conversation.domain.message import Source
from chatapp.knowledge.application.use_cases import CountKnowledge, SearchKnowledge


class KnowledgeContextGateway:
    def __init__(self, search: SearchKnowledge, count: CountKnowledge) -> None:
        self._search, self._count = search, count

    async def is_empty(self) -> bool:
        return await self._count.execute() == 0

    async def search(self, question: str, k: int) -> list[Source]:
        hits = await self._search.execute(question, k)
        return [Source(title=h.title, url=h.url, text=h.text, score=h.score) for h in hits]
```

Run the architecture test. It passes because this file is the one allowed crossing, and it only touches Knowledge's `application` layer.

**The HTTP adapter.** `chatapp/conversation/adapters/inbound/http.py`. Read how business errors become status codes **here and only here**, and how domain events become server-sent events:

```python
# needs: your backend folder (file: chatapp/conversation/adapters/inbound/http.py)
import json
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from chatapp.conversation.application.errors import ConversationError, ConversationNotFound, KnowledgeBaseEmpty, RateLimitExceeded
from chatapp.conversation.application.events import AnswerFailed, AnswerFinished, ChatEvent, SourcesFound, TokenGenerated
from chatapp.conversation.domain.conversation import InvalidQuestion

router = APIRouter(prefix="/api/conversations")

# Business errors become HTTP status codes here, and only here.
STATUS = {
    ConversationNotFound: (404, "Conversation not found"),
    RateLimitExceeded: (429, "Too many messages. Wait a minute."),
    KnowledgeBaseEmpty: (409, "The knowledge base is empty. Press Load OWASP Top 10 first."),
}


def to_http(error: Exception) -> HTTPException:
    if isinstance(error, InvalidQuestion):
        return HTTPException(status_code=422, detail=str(error))
    code, detail = STATUS.get(type(error), (500, "Something went wrong"))
    return HTTPException(status_code=code, detail=detail)


def container(request: Request):
    return request.app.state.container


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=4, ge=1, le=10)


def sse(event: ChatEvent) -> str:
    # One server-sent event: a line starting with "data:" and a blank line after it.
    match event:
        case TokenGenerated(text):
            body = {"type": "token", "text": text}
        case SourcesFound(sources):
            body = {"type": "sources", "sources": [asdict(s) for s in sources]}
        case AnswerFailed(message):
            body = {"type": "error", "message": message}
        case AnswerFinished():
            body = {"type": "done"}
    return f"data: {json.dumps(body)}\n\n"


@router.get("")
async def list_all(request: Request):
    conversations = await container(request).conversation.list_conversations.execute()
    return [{"id": c.id, "title": c.title} for c in conversations]


@router.post("")
async def create(request: Request):
    c = await container(request).conversation.start_conversation.execute()
    return {"id": c.id, "title": c.title}


@router.get("/{cid}/messages")
async def messages(cid: str, request: Request):
    try:
        found = await container(request).conversation.get_messages.execute(cid)
    except ConversationError as e:
        raise to_http(e)
    return [{"role": m.role.value, "content": m.content, "sources": [asdict(s) for s in m.sources]} for m in found]


@router.delete("/{cid}")
async def delete(cid: str, request: Request):
    await container(request).conversation.delete_conversation.execute(cid)
    return {"deleted": cid}


@router.post("/{cid}/chat")
async def chat(cid: str, body: ChatIn, request: Request):
    client_id = request.client.host if request.client else "unknown"
    try:
        stream = await container(request).conversation.send_message.execute(cid, body.message, body.k, client_id)
    except (ConversationError, InvalidQuestion) as e:
        raise to_http(e)

    async def events():
        async for event in stream.events():
            yield sse(event)

    return StreamingResponse(events(), media_type="text/event-stream")
```

### Why it works

The route is now thin: parse the request, call one use case, translate the result. The HTTP knowledge (status codes, JSON shape, SSE format) is all in one file. The domain stays clean.

---

## Step 10: The composition root, and switching over

### The idea

Something has to decide *which adapter fills which port*. That is the **composition root**. It is the only place that knows every concrete class, and it is allowed to, because it sits at the outer edge.

### Type this

`chatapp/container.py`. Read it top to bottom as a wiring diagram:

```python
# needs: your backend folder (file: chatapp/container.py)
"""The composition root: the ONE place that knows which adapter fills which port."""
from contextlib import asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis

from chatapp.conversation.adapters.outbound.knowledge_gateway import KnowledgeContextGateway
from chatapp.conversation.adapters.outbound.openai_answers import OpenAIAnswerGenerator
from chatapp.conversation.adapters.outbound.postgres_conversations import PostgresConversationRepository
from chatapp.conversation.adapters.outbound.redis_rate_limiter import RedisRateLimiter
from chatapp.conversation.application import use_cases as conversation_cases
from chatapp.infrastructure import db, settings
from chatapp.knowledge.adapters.outbound.celery_queue import CeleryJobQueue
from chatapp.knowledge.adapters.outbound.github_source import GithubOwaspSource
from chatapp.knowledge.adapters.outbound.markdown_splitter import MarkdownSplitter
from chatapp.knowledge.adapters.outbound.openai_embedder import OpenAIEmbedder
from chatapp.knowledge.adapters.outbound.pgvector_chunks import PgVectorChunkStore
from chatapp.knowledge.adapters.outbound.postgres_documents import PostgresDocumentRepository
from chatapp.knowledge.application import use_cases as knowledge_cases


@dataclass
class KnowledgeUseCases:
    load_knowledge_base: knowledge_cases.LoadKnowledgeBase
    ingest_document: knowledge_cases.IngestDocument
    list_knowledge: knowledge_cases.ListKnowledge


@dataclass
class ConversationUseCases:
    start_conversation: conversation_cases.StartConversation
    list_conversations: conversation_cases.ListConversations
    get_messages: conversation_cases.GetMessages
    delete_conversation: conversation_cases.DeleteConversation
    send_message: conversation_cases.SendMessage


@dataclass
class Container:
    knowledge: KnowledgeUseCases
    conversation: ConversationUseCases


@asynccontextmanager
async def build_container():
    pool = db.make_pool()
    await pool.open()
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        # Knowledge context: adapters first, then the use cases that need them.
        documents = PostgresDocumentRepository(pool)
        chunks = PgVectorChunkStore(pool)
        embedder = OpenAIEmbedder()
        knowledge = KnowledgeUseCases(
            load_knowledge_base=knowledge_cases.LoadKnowledgeBase(documents, CeleryJobQueue()),
            ingest_document=knowledge_cases.IngestDocument(documents, chunks, GithubOwaspSource(), MarkdownSplitter(), embedder),
            list_knowledge=knowledge_cases.ListKnowledge(documents),
        )
        # Conversation context. Its view of Knowledge goes through one gateway.
        gateway = KnowledgeContextGateway(knowledge_cases.SearchKnowledge(chunks, embedder), knowledge_cases.CountKnowledge(chunks))
        conversations = PostgresConversationRepository(pool)
        conversation = ConversationUseCases(
            start_conversation=conversation_cases.StartConversation(conversations),
            list_conversations=conversation_cases.ListConversations(conversations),
            get_messages=conversation_cases.GetMessages(conversations),
            delete_conversation=conversation_cases.DeleteConversation(conversations),
            send_message=conversation_cases.SendMessage(
                conversations, OpenAIAnswerGenerator(), gateway,
                RedisRateLimiter(redis, settings.RATE_LIMIT_PER_MINUTE), settings.HISTORY_LIMIT,
            ),
        )
        yield Container(knowledge=knowledge, conversation=conversation)
    finally:
        await pool.close()
        await redis.aclose()
```

`chatapp/main.py`. It builds the container once at start and hands it to the routes:

```python
# needs: your backend folder (file: chatapp/main.py)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatapp.container import build_container
from chatapp.conversation.adapters.inbound import http as conversation_http
from chatapp.infrastructure import db, settings
from chatapp.knowledge.adapters.inbound import http as knowledge_http


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    async with build_container() as container:
        app.state.container = container
        yield


app = FastAPI(title="OWASP Top 10 chat", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(conversation_http.router)
app.include_router(knowledge_http.router)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}
```

`chatapp/worker.py`. The entry point for Celery:

```python
# needs: your backend folder (file: chatapp/worker.py)
"""Entry point for the Celery worker:  celery -A chatapp.worker worker --loglevel=info"""
from chatapp.infrastructure.celery_app import celery_app
from chatapp.knowledge.adapters.inbound import celery_tasks  # noqa: F401  (importing it registers the task)

__all__ = ["celery_app"]
```

Start everything. Stop the old app first (`docker compose down` in `my-chat/`), then start the two databases and run the new code:

```bash
cd course2/fullstack-chat/my-chat
docker compose up -d postgres redis
cd backend
uv run uvicorn chatapp.main:app --reload --port 8000                # terminal 1
uv run celery -A chatapp.worker worker --loglevel=info --pool=solo  # terminal 2
```

Note the only differences from before: `chatapp.main:app` instead of `main:app`, and `-A chatapp.worker` instead of `-A tasks`.

Now the moment of truth. **Run the same live test, unchanged**, apart from its imports (it now takes the Celery app and the rate limiter from the new package; copy the new `test_live.py` from [../app-hexagonal/backend/test_live.py](../app-hexagonal/backend/test_live.py)):

```bash
uv run python test_live.py
uv run python -m tests.test_domain
uv run python -m tests.test_architecture
```

**What you should see:**

```
ALL LIVE TESTS PASSED
DOMAIN TESTS PASSED
ARCHITECTURE TESTS PASSED
```

The frontend works as before, because the HTTP contract did not change. Open http://localhost:3000, press **Load OWASP Top 10**, and chat.

### Why it works

Every HTTP and Celery request now flows: inbound adapter, then a use case, then ports, then outbound adapters, then technology. Behaviour is identical, because the tests that describe behaviour do not know the structure changed.

### Common problems

| Problem | What you see | Fix |
|---|---|---|
| Circular import | `ImportError ... partially initialized module` | A file imports an outer layer. Run the architecture test, then move the import or the class. |
| Forgot `__init__.py` | `ModuleNotFoundError: chatapp...` | `find chatapp tests -type d -exec touch {}/__init__.py \;` |
| Old command | `Error loading ASGI app` | Use `uvicorn chatapp.main:app` and `celery -A chatapp.worker`. |
| Worker has no task | Documents stay `queued` | The worker imports `celery_tasks` in `worker.py`. Check the banner lists `knowledge.ingest_document`. |
| Domain imports a library | Architecture test fails | Move that code to an adapter. |

---

## Step 11: Docker, and what you gained

### Docker: three small changes

The Dockerfiles from [part 5](05-docker-compose.md) barely change. In `backend/Dockerfile`, the start command points at the new module:

```dockerfile
CMD ["uvicorn", "chatapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

In `docker-compose.yml`, the worker command and its health check point at the new entry:

```yaml
    command: ["celery", "-A", "chatapp.worker", "worker", "--loglevel=info", "--concurrency=2"]
    ...
      test: ["CMD-SHELL", "celery -A chatapp.worker inspect ping -d celery@$$HOSTNAME || exit 1"]
```

Also set `name: owasp-chat-hex` at the top of the compose file, so this version's volumes never mix with the layered version's. Then `docker compose up --build` and run `uv run python test_live.py` as before.

### What you gained

| Before | After |
|---|---|
| "First message names the chat" is a SQL `WHERE` | A method on `Conversation`, tested in milliseconds |
| Status strings in many files | `Document` with a life cycle |
| One route that does everything | A thin route and a use case you can read top to bottom |
| Replacing a technology touches many files | One adapter file and one wiring line |
| Rules live in a document | An architecture test fails when they are broken |
| The worker imports web helpers | The worker calls the same use cases as the API |

### An honest look at the cost

- **More files, more indirection.** The layered app has about 12 backend files. This has about 40. For a tutorial app that is a lot of ceremony.
- **The domain is small.** Most of this app is "move data between technologies". The real rules (titles, document life cycle, "sources must exist") fit on one page. DDD earns its keep when the rules are rich. Use this structure when you expect the rules to grow, or to learn the pattern, not by reflex.
- **Testing without services is limited here.** Pure domain tests are easy. Testing a use case without Postgres or OpenAI means supplying substitutes for the ports (in-memory implementations). This repo's rule is *real services, no fakes*, so use cases are tested through the live test. If you ever add in-memory adapters, the ports make that easy, and you must keep a live test too.
- **Two async worlds.** Celery jobs are synchronous, but the adapters are async. The job bridges with `asyncio.run` and builds a container per job. Fine for a few jobs, wasteful for thousands.

---

## Practice

No answers shown. Ask me for a hint.

1. **Swap an adapter.** Write a second `Embedder` that uses a different embedding model. Which files change? (Remember `vector(1536)` in `schema.sql`.)
2. **A new inbound adapter.** Add a command-line adapter that calls `SearchKnowledge` and prints hits. Which layers does it touch?
3. **A new rule.** "A conversation may have at most 200 messages." Where does it live, and which tests do you add?
4. **A third context.** Imagine *Accounts* (users, plans). Where does it plug in, and what stops it from reaching into Conversation's tables?
5. **Events instead of a gateway.** Instead of Conversation asking Knowledge directly, imagine Knowledge publishing `DocumentReady`. What would change, and what would get harder?
6. **Break the rules on purpose.** Import `psycopg` in a domain file, then import Knowledge's `Document` from a Conversation use case. Read both architecture test failures.
7. **Explain it.** In eight sentences, explain to a friend the difference between a context, a port and an adapter, using the OWASP chat as the example.

## Cheat sheet

| Question | Answer |
|---|---|
| Where do business rules go? | `domain/` (plain Python, no technology). |
| Where do "things a user can do" go? | `application/use_cases.py`. |
| Where do I describe what I need from outside? | `application/ports.py`, named for the need. |
| Where does technology go? | `adapters/outbound/`. |
| Where do HTTP routes and Celery jobs go? | `adapters/inbound/`. |
| Who decides which adapter fills which port? | `container.py`, the composition root. |
| How do contexts talk? | Through one gateway that calls the other's use cases and translates. |
| What keeps the rules honest? | `tests/test_architecture.py`. |
| What proves behaviour did not change? | `test_live.py`, unchanged. |

| Layer | May import |
|---|---|
| `domain` | the standard library and `shared` |
| `application` | its own `domain`, `shared`, its own ports |
| `adapters` | `application`, `domain`, technology libraries |
| `container.py`, `main.py`, `worker.py` | everything (the outer edge) |

Back to the [guide](../README.md).
