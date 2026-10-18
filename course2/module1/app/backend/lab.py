"""The lab's RAG pipeline as an object: load, split, embed, store, retrieve."""
import os
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from psycopg_pool import ConnectionPool

load_dotenv()

POLICY_URL = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/6JDbUb_L3egv_eOkouY71A.txt"
# DATA_DIR lets a container keep the downloaded file on a volume.
POLICY_FILE = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent / "data")) / "companyPolicies.txt"


def load_policies() -> str:
    # Downloaded once, like the lab's wget step.
    if not POLICY_FILE.exists():
        POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(POLICY_URL, POLICY_FILE)
    return POLICY_FILE.read_text()


class Lab:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text = load_policies()

    def is_built(self) -> bool:
        with self.pool.connection() as conn:
            return conn.execute("SELECT 1 FROM lab_chunks LIMIT 1").fetchone() is not None

    def build(self, splitter: str, chunk_size: int, chunk_overlap: int) -> None:
        cls = CharacterTextSplitter if splitter == "character" else RecursiveCharacterTextSplitter
        chunks = cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap).split_documents(
            [Document(page_content=self.text, metadata={"source": POLICY_FILE.name})]
        )
        texts = [c.page_content for c in chunks]
        vectors = self.embeddings.embed_documents(texts)
        with self.pool.connection() as conn, conn.transaction():  # all or nothing, so a failure keeps the old index
            conn.execute("DELETE FROM lab_chunks")  # replace the whole index, so old chunks do not linger
            for i, (text, vec) in enumerate(zip(texts, vectors)):
                conn.execute("INSERT INTO lab_chunks (id, content, embedding) VALUES (%s, %s, %s)", (i, text, np.array(vec)))
            conn.execute(
                "INSERT INTO lab_settings (id, splitter, chunk_size, chunk_overlap) VALUES (1, %s, %s, %s) "
                "ON CONFLICT (id) DO UPDATE SET splitter = excluded.splitter, "
                "chunk_size = excluded.chunk_size, chunk_overlap = excluded.chunk_overlap",
                (splitter, chunk_size, chunk_overlap),
            )

    def state(self) -> dict:
        with self.pool.connection() as conn:
            settings = conn.execute("SELECT splitter, chunk_size, chunk_overlap FROM lab_settings").fetchone()
            rows = conn.execute("SELECT id, length(content) AS length, content AS text FROM lab_chunks ORDER BY id").fetchall()
        return {"settings": settings, "chunks": rows}

    def search(self, question: str, k: int) -> list[dict]:
        vec = np.array(self.embeddings.embed_query(question))
        with self.pool.connection() as conn:
            # <=> is pgvector's cosine DISTANCE (0 = same direction). 1 - distance = similarity.
            rows = conn.execute(
                "SELECT id, content AS text, 1 - (embedding <=> %s) AS score FROM lab_chunks ORDER BY embedding <=> %s LIMIT %s",
                (vec, vec, k),
            ).fetchall()
        return [{**r, "score": round(float(r["score"]), 4)} for r in rows]
