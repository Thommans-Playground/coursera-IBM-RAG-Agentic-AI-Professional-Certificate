"""Prompts and the question-answering step. It uses a Lab only to search."""
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from lab import Lab

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


def answer(lab: Lab, question: str, k: int, strict: bool, history: list[dict]):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=300)
    messages = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
    standalone = question
    if messages:
        standalone = (REWRITE | llm | StrOutputParser()).invoke({"history": messages, "question": question})
    hits = lab.search(standalone, k)
    context = "\n\n".join(h["text"] for h in hits)
    prompt = ChatPromptTemplate.from_template(STRICT if strict else LOOSE)
    reply = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": standalone})
    return reply, standalone, hits
