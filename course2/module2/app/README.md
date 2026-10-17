# RAG Notes Bot (Next.js + FastAPI)

A web app version of the module 1 notes bot. It replaces the Gradio interface from the course.

| Part | Folder | Tech |
|---|---|---|
| Backend (RAG engine and API) | `backend/` | FastAPI, LangChain, OpenAI |
| Frontend (the web page) | `frontend/` | Next.js, TypeScript, Tailwind, shadcn/ui |

## Run it

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

## Check without spending money

```bash
cd course2/module2/app/backend && uv run python -c "import test_api; test_api.test_all(); print('ok')"
cd ../frontend && npx tsc --noEmit && npm run lint && npm run build
```

The backend test uses fake models, so it proves the wiring, not real answers.

Learn how it is built: [tutorials](../tutorials/).
