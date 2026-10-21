# RAG Notes Bot (Next.js + FastAPI)

A web app version of the module 1 notes bot. It replaces the Gradio interface from the course.

| Part | Folder | Tech |
|---|---|---|
| Backend (RAG engine and API) | `backend/` | FastAPI, LangChain, OpenAI |
| Frontend (the web page) | `frontend/` | Next.js, TypeScript, Tailwind, shadcn/ui |

## Run it with Docker

```bash
cd course2/module2/app
cp .env.example .env        # then put your key in .env as OPENAI_API_KEY=sk-...
docker compose up --build
```

Open http://localhost:3000. Already have the key in the repo-root `.env`? Run `docker compose --env-file ../../../.env up --build`. Your module 1 notes (`course2/module1/transcript.md`) are mounted read-only into the backend so the bot has something to read. `docker compose down` stops everything. The index is in memory, so uploads vanish when the backend restarts. The [tutorial](../tutorials/02-build-the-rag-web-app.md#step-9-run-it-with-docker) builds these files step by step.

## Run it without Docker


You need `OPENAI_API_KEY` in the repo-root `.env`. Use two terminals.

```bash
# Terminal 1: backend, from the repo root
cd course2/module2/app/backend
uv run uvicorn main:app --reload --port 8000

# Terminal 2: frontend
cd course2/module2/app/frontend
npm install
npm run dev
```

Open http://localhost:3000. The API docs are at http://localhost:8000/docs.

The frontend reads the API address from `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Test the real stack

No fakes. With the backend running (either way above), this calls the real OpenAI API (a fraction of a cent):

```bash
cd course2/module2/app/backend && uv run python test_live.py
cd ../frontend && npx tsc --noEmit && npm run lint && npm run build
```

It uploads a file with a made-up fact and checks the bot answers with it, that an unrelated question gets "I don't know", that follow-ups work with history, and that bad input gets `422`.

Learn how it is built: [tutorials](../tutorials/).
