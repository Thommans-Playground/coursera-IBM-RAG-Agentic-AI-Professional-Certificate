"""Splitting and embedding. No web code and no database code in here."""
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

import settings

# Markdown-aware: prefers to cut at headings and paragraphs, not mid-sentence.
splitter = RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=1000, chunk_overlap=150)


def embedder() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.EMBED_MODEL)


def split(text: str) -> list[Document]:
    return splitter.create_documents([text])


def for_embedding(title: str, chunk: str) -> str:
    # A chunk like "Use parameterized queries" does not say which category it belongs to.
    # Putting the title in front helps the vector land near the right topic.
    return f"{title}\n\n{chunk}"


async def embed_query(question: str) -> list[float]:
    return await embedder().aembed_query(question)
