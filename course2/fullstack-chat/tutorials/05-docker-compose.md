# Tutorial 5: Run Everything With Docker

**What you build.** One command that starts the whole OWASP chatbot: Postgres with pgvector, Redis, the API, the Celery worker and the Next.js page. Until now you ran five things in separate terminals. After this tutorial, you run one.

This is part 5 of 5. You need [part 4](04-redis-and-celery.md) working, so you know what each piece does:

| Part | Adds |
|---|---|
| [1](01-hello-world-to-streaming-chat.md) | Streaming chat |
| [2](02-postgres-conversations.md) | Postgres: saved conversations |
| [3](03-pgvector-owasp-knowledge-base.md) | pgvector: the OWASP knowledge base and RAG |
| [4](04-redis-and-celery.md) | Redis and Celery: background loading, rate limiting |
| **5** | **Docker: one command to run it all** |

> **Ports.** The Docker setup uses ports 3000, 8000, 5432 and 6379. Stop the dev servers and any containers from the earlier parts first (`docker compose down` in `my-chat/`), or you will see "port is already allocated".

## The problem

To run the app you now need Python and its packages, Node and its packages, a Postgres container, a Redis container, a Celery worker, the right environment variables, and five terminals. A friend (or you in six months) will get at least one of those wrong.

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
celery==5.6.3
redis==8.1.0
psycopg[binary]==3.3.6
psycopg-pool==3.3.3
pgvector==0.5.1
numpy==2.5.4
langchain-core==1.6.10
langchain-openai==1.7.2
langchain-text-splitters==1.1.3
python-dotenv==1.2.4
pydantic==2.14.1
httpx==0.28.1
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
# Run as a normal user, not root.
RUN useradd --create-home --uid 10001 app
COPY --chown=app . .
USER app
```

Say which port it uses, how Docker can tell it is healthy, and how to start it. `--host 0.0.0.0` is needed so the app accepts connections from outside the container:

```dockerfile
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/hello', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add `backend/.dockerignore` so junk does not get copied into the image:

```text
__pycache__/
*.pyc
.env
test_live.py
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

**5. The compose file.** Replace `docker-compose.yml`. (The earlier parts' version had only Postgres and Redis.) It has five services. `postgres` and `redis` use ready-made images. The `backend` and `worker` are built from your backend Dockerfile. The `frontend` has its own.

```yaml
name: owasp-chat   # a fixed project name, so volumes do not clash with the other apps in this repo

services:
  postgres:
    image: pgvector/pgvector:pg17   # Postgres with the pgvector extension installed
    environment:
      POSTGRES_USER: chat
      POSTGRES_PASSWORD: chat
      POSTGRES_DB: chat
    ports:
      - "5432:5432"   # published so you can also run the API on your machine
    volumes:
      - pgdata:/var/lib/postgresql/data   # keeps your data when the container restarts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chat"]
      interval: 3s
      retries: 20
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 3s
      retries: 20
    restart: unless-stopped

  backend:
    build: ./backend
    environment: &backend-env   # shared with the worker below
      OPENAI_API_KEY: ${OPENAI_API_KEY:?Set OPENAI_API_KEY in app/.env (copy .env.example)}
      DATABASE_URL: postgresql://chat:chat@postgres:5432/chat   # "postgres" is the service name on the Docker network
      REDIS_URL: redis://redis:6379/0
      FRONTEND_ORIGINS: http://localhost:3000,http://127.0.0.1:3000
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  worker:
    build: ./backend   # the same image as the API, a different command
    command: ["celery", "-A", "tasks", "worker", "--loglevel=info", "--concurrency=2"]
    environment: *backend-env
    depends_on:
      backend:
        condition: service_healthy   # the API creates the tables on start
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "celery -A tasks inspect ping -d celery@$$HOSTNAME || exit 1"]
      interval: 15s
      timeout: 10s
      start_period: 20s
      retries: 3
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
| `worker` uses `build: ./backend` with a `command` | The worker is the **same image** as the API with a different start command. One build, two roles. |
| `environment: &backend-env` and `*backend-env` | A YAML anchor: define the settings once, reuse them in the worker. |
| `redis://redis:6379` and `postgres:5432` | Inside Docker, services reach each other by **service name**. |
| The worker `healthcheck` | Asks Celery itself (`inspect ping`) whether the worker answers. A running process is not always a working one. |
| The worker `depends_on` the backend | The API creates the tables when it starts, and the worker needs them. |
| `--concurrency=2` | Two jobs at once. Docker uses the normal Celery pool, so no `--pool=solo` is needed on Linux. |

### Run it

```bash
cd course2/fullstack-chat/my-chat
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
cd course2/fullstack-chat/my-chat/backend
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

## Practice

No answers shown. Ask me for a hint.

1. **Scale the worker.** Run three workers with `docker compose up --scale worker=3`. What changes in the logs while loading the knowledge base?
2. **Break the health check.** Change the health check URL to a path that does not exist. What does `docker compose ps` show, and what happens to the services that depend on it?
3. **Smaller image.** Check `docker images`. Which image is biggest, and what in the Dockerfile decides that?
4. **Secrets.** The database password `chat` is in the compose file. Move it to `.env` and reference it with ``.
5. **Do not publish the database.** Remove the `ports` lines for `postgres` and `redis`. What stops working from your laptop (the live test?), and what still works?
6. **Explain it.** In six sentences, explain why `NEXT_PUBLIC_API_URL` is `localhost:8000` but `DATABASE_URL` says `postgres`.

## Cheat sheet

| Need | Command |
|---|---|
| Start everything | `docker compose up --build` (add `-d` to detach) |
| Status and health | `docker compose ps` |
| One service's log | `docker compose logs -f worker` |
| A shell or a command inside | `docker compose exec backend id -u` |
| Rebuild after code changes | `docker compose up --build` |
| Stop | `docker compose down` |
| Stop and delete data | `docker compose down -v` |
| Only the databases (for dev) | `docker compose up -d postgres redis` |

Back to the [guide](../README.md).
