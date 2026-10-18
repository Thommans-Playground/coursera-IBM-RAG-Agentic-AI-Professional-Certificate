# RAG Lab Web App (Next.js + FastAPI)

The Module 1 lab, *Summarize private documents using RAG, LangChain and LLMs*, as a web app. Instead of notebook cells you get three tabs: **Chunks** (see how splitting works), **Search** (see what the retriever returns) and **Ask** (chat, with the "I don't know" rule and memory as switches).

| Part | Folder | Tech |
|---|---|---|
| Backend (RAG pipeline and API) | `backend/` | FastAPI, LangChain, OpenAI |
| Vector store | `postgres` service | PostgreSQL 17 with pgvector (replaces the lab's in-memory store) |
| Frontend | `frontend/` | Next.js, TypeScript, Tailwind, shadcn/ui |

## Run it with Docker (recommended)

One command starts all three parts (Postgres with pgvector, the API, the page). You only need Docker and your OpenAI key.

```bash
cd course2/module1/app
cp .env.example .env        # then put your key in .env as OPENAI_API_KEY=sk-...
docker compose up --build
```

Open http://localhost:3000. The API is at http://localhost:8000 (docs at `/docs`).

Already have the key in the repo-root `.env`? Skip the copy and run `docker compose --env-file ../../../.env up --build`.

| Command | Does |
|---|---|
| `docker compose up --build -d` | Build and start in the background |
| `docker compose ps` | Show status and health |
| `docker compose logs -f backend` | Follow the backend log |
| `docker compose down` | Stop and remove the containers (the index stays in a volume) |
| `docker compose down -v` | Also delete the volume |

What is in the setup:

| File | Job |
|---|---|
| `docker-compose.yml` | Three services (`postgres`, `backend`, `frontend`), volumes for the database and the downloaded file, health checks, start order, restart policy |
| `backend/Dockerfile` | Python image, pinned `requirements.txt`, runs as a non-root user, health check on `/api/health` |
| `frontend/Dockerfile` | Multi-stage build (install, build, small runtime image), Next.js `standalone` output, non-root user |
| `.env.example` | The one setting you must provide |

Notes:

- **The API address is fixed at build time.** `NEXT_PUBLIC_API_URL` is written into the JavaScript when the frontend image is built. It must be the address your **browser** uses (`http://localhost:8000`), not a Docker service name. To change it, edit `args` in `docker-compose.yml` and rebuild.
- **A missing key stops the start** with a clear message, instead of failing later on the first question.
- **Changed code?** Run `docker compose up --build` again. For fast edits while developing, use the manual steps below.

## Run it without Docker

Faster for editing code. You still need Postgres, which Docker provides in one line. Use three terminals, with `OPENAI_API_KEY` in the repo-root `.env`.

```bash
# Terminal 1: Postgres only
cd course2/module1/app
docker compose up -d postgres

# Terminal 2: backend (creates the tables, downloads the policy file, builds the first index)
cd course2/module1/app/backend
uv run uvicorn main:app --reload --port 8000

# Terminal 3: frontend
cd course2/module1/app/frontend
npm install
npm run dev
```

Open http://localhost:3000. API docs: http://localhost:8000/docs. This app, the [module 2 app](../../module2/app/) and the [OWASP chat](../../fullstack-chat/app/) share ports 3000, 8000 and (for Postgres) 5432, so run one at a time.

The index lives in Postgres, so it survives restarts. Rebuilding with new settings in the Chunks tab replaces it.

## Test the real stack

No fakes. With Postgres and the API running (either way above), this calls the real database and the real OpenAI API (a fraction of a cent):

```bash
cd course2/module1/app/backend && uv run python test_live.py
cd ../frontend && npx tsc --noEmit && npm run lint && npm run build
```

It checks that the lab's splitter gives 16 chunks (with tiny heading-only ones), that the index comes back from Postgres, that search finds the smoking policy, that the "I don't know" rule works on the lab's trap question, and that a follow-up is rewritten using the history.

### Why Postgres and no Redis?

| Question | Answer |
|---|---|
| Why Postgres? | The lab's in-memory store forgets everything on restart and re-embeds every time. With pgvector the vectors live in a table, the search is one SQL query, and the index persists. |
| Why no Redis? | Nothing here needs it: there is no job queue and no rate limiting. The [OWASP chat](../../fullstack-chat/README.md) adds Redis and Celery when background loading and rate limits appear. |

Learn how it is built: [Tutorial 3](../tutorials/03-build-the-rag-lab-web-app.md).
