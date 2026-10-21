"""The RAG engine: split, embed, store, retrieve, answer. No web code in here."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

ALLOWED_MODELS = {"gpt-4o-mini", "gpt-4o"}
STYLES = {
    "concise": "Answer in one or two sentences.",
    "detailed": "Answer in a short paragraph with the key details.",
}

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    "Answer using only the context. If the answer is not in the context, "
    "say \"I don't know\". {style}\n\nContext:\n{context}\n\nQuestion: {question}"
)
REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's last question so it makes sense on its own, "
               "using the chat history. Return only the question."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])

# Course notes from module 1, so the bot has something to read on first start.
# SEED_FILE lets a container mount the notes at another path.
# The default is course2/module1/transcript.md. `.parent` stops at the root, so it never raises.
SEED_FILE = Path(os.getenv("SEED_FILE") or Path(__file__).resolve().parent.parent.parent.parent / "module1" / "transcript.md")


class RagEngine:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.store = InMemoryVectorStore(self.embeddings)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100, add_start_index=True
        )
        self.sources: dict[str, int] = {}  # file name -> number of chunks

    def add_text(self, name: str, text: str) -> int:
        chunks = self.splitter.split_documents([Document(page_content=text, metadata={"source": name})])
        self.store.add_documents(chunks)
        self.sources[name] = self.sources.get(name, 0) + len(chunks)
        return len(chunks)

    def seed(self) -> None:
        if SEED_FILE.exists() and not self.sources:
            self.add_text(SEED_FILE.name, SEED_FILE.read_text())

    def ask(self, question: str, history: list[dict], k: int, model: str, style: str) -> tuple[str, list[Document]]:
        llm = ChatOpenAI(model=model, temperature=0, max_tokens=400)
        messages = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
        # Rewrite follow-ups so the retriever searches with a complete question.
        standalone = question
        if messages:
            standalone = (REWRITE_PROMPT | llm | StrOutputParser()).invoke({"history": messages, "question": question})
        docs = self.store.as_retriever(search_kwargs={"k": k}).invoke(standalone)
        context = "\n\n".join(d.page_content for d in docs)
        answer = (ANSWER_PROMPT | llm | StrOutputParser()).invoke(
            {"context": context, "question": standalone, "style": STYLES[style]}
        )
        return answer, docs
