"""Split, embed, and find the closest chunks. No web and no Redis in here."""
import numpy as np
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import settings

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100, add_start_index=True)


def embedder() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.EMBED_MODEL)


def split(name: str, text: str) -> list[Document]:
    return splitter.split_documents([Document(page_content=text, metadata={"source": name})])


async def embed_query(question: str) -> list[float]:
    return await embedder().aembed_query(question)


def top_k(query_vec: list[float], chunks: list[dict], k: int) -> list[dict]:
    if not chunks:
        return []
    matrix = np.array([c["vec"] for c in chunks])
    q = np.array(query_vec)
    scores = matrix @ q / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q))  # cosine similarity
    best = np.argsort(scores)[::-1][:k]
    return [
        {"source": chunks[i]["source"], "start_index": chunks[i]["start_index"], "text": chunks[i]["text"], "score": round(float(scores[i]), 4)}
        for i in best
    ]
