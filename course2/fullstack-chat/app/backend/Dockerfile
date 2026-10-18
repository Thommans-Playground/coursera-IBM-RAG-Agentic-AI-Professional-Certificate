# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first, so code changes do not reinstall everything.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run as a normal user, not root.
RUN useradd --create-home --uid 10001 app
COPY --chown=app . .
USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/hello', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
