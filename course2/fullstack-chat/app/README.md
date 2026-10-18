# Finished app: full-stack chat

The result of [the three tutorials](../tutorials/). Compare your own `my-chat/` folder with this one.

```text
app/
  docker-compose.yml      Redis
  backend/                FastAPI, Celery, LangChain
    main.py  chat.py  conversations.py  docs.py   routes
    store.py  deps.py  settings.py                Redis access and config
    llm.py  rag.py  tasks.py                      model, retrieval, background job
    test_api.py                                   free tests (fake Redis, fake models)
  frontend/               Next.js, TypeScript, Tailwind, shadcn/ui
```

Run instructions are in the [guide](../README.md#5-run-the-finished-app). In short: `docker compose up -d`, `uv run uvicorn main:app --reload --port 8000`, `uv run celery -A tasks worker --loglevel=info --pool=solo` (both in `backend/`), and `npm run dev` in `frontend/`.
