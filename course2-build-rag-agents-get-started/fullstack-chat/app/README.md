# Finished app: OWASP Top 10 chatbot

The result of [the four tutorials](../tutorials/). Compare your own `my-chat/` folder with this one.

```text
app/
  docker-compose.yml      Postgres (with pgvector), Redis, API, worker, page: one command
  backend/                FastAPI, Celery, LangChain
    main.py  chat.py  conversations.py  knowledge.py   routes
    schema.sql  db.py  store.py  deps.py  settings.py  Postgres and config
    owasp.py  rag.py  llm.py                           OWASP pages, splitting and embedding, prompts
    tasks.py  ratelimit.py                             Celery job, Redis rate limit
    test_live.py                                       tests against the real stack
  frontend/               Next.js, TypeScript, Tailwind, shadcn/ui
```

Run instructions are in the [guide](../README.md#5-run-the-finished-app). In short: `cp .env.example .env` (add your key) and `docker compose up --build`. For development: `docker compose up -d postgres redis`, then in `backend/`: `uv run uvicorn main:app --reload --port 8000` and `uv run celery -A tasks worker --loglevel=info --pool=solo`, and `npm run dev` in `frontend/`. Press **Load OWASP Top 10** in the page.

Content from the OWASP Top 10:2025 is © OWASP Foundation, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
