"""The lab's RAG pipeline as an object: load, split, embed, store, retrieve, answer."""
from pathlib import Path
from urllib.request import urlretrieve

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

load_dotenv()

POLICY_URL = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/6JDbUb_L3egv_eOkouY71A.txt"
POLICY_FILE = Path(__file__).resolve().parent / "data" / "companyPolicies.txt"

# The lab's first prompt has no safety rule. The second is the "I don't know" version.
LOOSE = "Use the context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}"
STRICT = (
    "Use only the context below to answer the question at the end. "
    "If the answer is not in the context, say \"I don't know\". "
    "Do not make up an answer.\n\nContext:\n{context}\n\nQuestion: {question}"
)
REWRITE = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's last question so it makes sense on its own, "
               "using the chat history. Return only the question."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])


def load_policies() -> str:
    # Downloaded once, like the lab's wget step.
    if not POLICY_FILE.exists():
        POLICY_FILE.parent.mkdir(exist_ok=True)
        urlretrieve(POLICY_URL, POLICY_FILE)
    return POLICY_FILE.read_text()


class Lab:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text = load_policies()
        self.chunks: list[Document] = []
        self.store = InMemoryVectorStore(self.embeddings)
        self.settings: dict = {}

    def build(self, splitter: str, chunk_size: int, chunk_overlap: int) -> None:
        cls = CharacterTextSplitter if splitter == "character" else RecursiveCharacterTextSplitter
        docs = cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap).split_documents(
            [Document(page_content=self.text, metadata={"source": POLICY_FILE.name})]
        )
        for i, d in enumerate(docs):
            d.metadata["chunk_id"] = i
        self.chunks = docs
        self.store = InMemoryVectorStore(self.embeddings)  # fresh store, so old chunks do not linger
        self.store.add_documents(docs)
        self.settings = {"splitter": splitter, "chunk_size": chunk_size, "chunk_overlap": chunk_overlap}

    def search(self, question: str, k: int) -> list[tuple[Document, float]]:
        return self.store.similarity_search_with_score(question, k=k)

    def ask(self, question: str, k: int, strict: bool, history: list[dict]):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=300)
        messages = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
        standalone = question
        if messages:
            standalone = (REWRITE | llm | StrOutputParser()).invoke({"history": messages, "question": question})
        hits = self.search(standalone, k)
        context = "\n\n".join(d.page_content for d, _ in hits)
        prompt = ChatPromptTemplate.from_template(STRICT if strict else LOOSE)
        answer = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": standalone})
        return answer, standalone, hits
