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
