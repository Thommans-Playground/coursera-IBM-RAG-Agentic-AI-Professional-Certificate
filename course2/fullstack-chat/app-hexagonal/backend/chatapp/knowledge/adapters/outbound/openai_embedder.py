from langchain_openai import OpenAIEmbeddings

from chatapp.infrastructure import settings


class OpenAIEmbedder:
    def __init__(self) -> None:
        self.model = OpenAIEmbeddings(model=settings.EMBED_MODEL)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self.model.aembed_documents(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self.model.aembed_query(text)
