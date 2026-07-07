from __future__ import annotations

from typing import Iterable

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import DEFAULT_GEMINI_MODEL


SYSTEM_PROMPT = (
    "You are SchemeSense AI, a grounded assistant for Indian government scheme documents. "
    "Answer only from the provided context. If the context does not cover the question, say so explicitly. "
    "Do not invent facts. Keep official scheme names unchanged unless the user language requires otherwise."
)


def build_chat_model(model_name: str = DEFAULT_GEMINI_MODEL, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)


def _context_block(documents) -> str:
    parts: list[str] = []
    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        parts.append(
            "\n".join(
                [
                    f"[Chunk {index}]",
                    f"Source: {metadata.get('source_file')} | Page: {metadata.get('document_page_number')} | Chunk: {metadata.get('chunk_id')}",
                    f"Snippet: {document.page_content}",
                ]
            )
        )
    return "\n\n".join(parts)


def answer_question(model: ChatGoogleGenerativeAI, question: str, documents) -> str:
    prompt = (
        f"Question: {question}\n\n"
        f"Context:\n{_context_block(documents)}\n\n"
        "Write a concise answer grounded only in the context. If the answer is not covered, say 'The documents do not cover this question.'"
    )
    response = model.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return getattr(response, "content", str(response)).strip()


def translate_text(model: ChatGoogleGenerativeAI, text: str, target_language: str) -> str:
    if target_language.lower() == "en":
        return text
    prompt = (
        f"Translate the following text into {target_language}. Preserve official scheme names and legal terms. "
        f"Return only the translation.\n\n{text}"
    )
    response = model.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return getattr(response, "content", str(response)).strip()


def compare_documents(model: ChatGoogleGenerativeAI, topic: str, left_document, right_document) -> str:
    prompt = (
        f"Topic: {topic}\n\n"
        f"Document A context:\n{_context_block(left_document)}\n\n"
        f"Document B context:\n{_context_block(right_document)}\n\n"
        "Decide whether the documents conflict on the topic. Explain briefly and say 'No conflict found' if appropriate."
    )
    response = model.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return getattr(response, "content", str(response)).strip()
