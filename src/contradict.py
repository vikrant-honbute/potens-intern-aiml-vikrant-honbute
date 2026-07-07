from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from .config import DEFAULT_ARTIFACT_DIR, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_CORPUS_DIR
from .llm import build_chat_model, compare_documents
from .retrieval import build_hybrid_retriever


def _matches_document_id(document: Document, document_id: str) -> bool:
    source_file = str(document.metadata.get("source_file", ""))
    source_title = str(document.metadata.get("document_title", ""))
    normalized = document_id.lower().strip()
    return normalized in source_file.lower() or normalized in source_title.lower() or normalized in Path(source_file).stem.lower()


def collect_topic_chunks(document_id: str, topic: str, corpus_dir: Path = DEFAULT_CORPUS_DIR, index_dir: Path = DEFAULT_ARTIFACT_DIR) -> list[Document]:
    retriever = build_hybrid_retriever(corpus_dir=corpus_dir, index_dir=index_dir, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP)
    docs = retriever.invoke(topic)
    matched = [doc for doc in docs if _matches_document_id(doc, document_id)]
    return matched[:3]


def contradict_documents(document_a: str, document_b: str, topic: str, model_name: str | None = None) -> str:
    left = collect_topic_chunks(document_a, topic)
    right = collect_topic_chunks(document_b, topic)
    model = build_chat_model(model_name=model_name or None, temperature=0.0)
    return compare_documents(model, topic, left, right)
