# RAG Lab Web App (Next.js + FastAPI)

The Module 1 lab, *Summarize private documents using RAG, LangChain and LLMs*, as a web app. Instead of notebook cells you get three tabs: **Chunks** (see how splitting works), **Search** (see what the retriever returns) and **Ask** (chat, with the "I don't know" rule and memory as switches).

| Part | Folder | Tech |
|---|---|---|
| Backend (RAG pipeline and API) | `backend/` | FastAPI, LangChain, OpenAI |
| Frontend | `frontend/` | Next.js, TypeScript, Tailwind, shadcn/ui |

## Run it

You need `OPENAI_API_KEY` in the repo-root `.env`. Use two terminals. The backend downloads the lab's `companyPolicies.txt` into `backend/data/` the first time.

```bash
# Terminal 1: backend
cd course2/module1/app/backend
uv run uvicorn main:app --reload --port 8000

# Terminal 2: frontend
cd course2/module1/app/frontend
npm install
npm run dev
```

Open http://localhost:3000. API docs: http://localhost:8000/docs. Both this app and the [module 2 app](../../module2/app/) use port 3000, so run one at a time.

## Check without spending money

```bash
cd course2/module1/app/backend && uv run python -c "import test_api; test_api.test_all(); print('ok')"
cd ../frontend && npx tsc --noEmit && npm run lint && npm run build
```

The test uses fake models. It proves the wiring (for example that the lab's splitter gives 16 chunks), not real answers.

Learn how it is built: [Tutorial 3](../tutorials/03-build-the-rag-lab-web-app.md).
