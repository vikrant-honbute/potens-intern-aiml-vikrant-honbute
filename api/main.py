from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import DEFAULT_ARTIFACT_DIR, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_CORPUS_DIR, DEFAULT_GEMINI_MODEL
from src.ingest import discover_pdf_files
from src.llm import answer_question, build_chat_model
from src.rerank import build_reranked_retriever
from src.translate import detect_language, translate_answer_from_english, translate_query_to_english
from src.contradict import contradict_documents


app = FastAPI(title="SchemeSense AI")


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)


class Citation(BaseModel):
    source_file: str | None = None
    document_page_number: int | None = None
    chunk_id: str | None = None
    snippet: str | None = None


class AskResponse(BaseModel):
    answer: str
    detected_language: str
    translated_query: str | None = None
    citations: list[Citation]


class ContradictRequest(BaseModel):
    document_a: str = Field(..., min_length=1)
    document_b: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)


class ContradictResponse(BaseModel):
    document_a: str
    document_b: str
    topic: str
    result: str


@lru_cache(maxsize=1)
def _retriever():
    return build_reranked_retriever(
        corpus_dir=DEFAULT_CORPUS_DIR,
        index_dir=DEFAULT_ARTIFACT_DIR,
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )


@lru_cache(maxsize=1)
def _chat_model():
    return build_chat_model(model_name=DEFAULT_GEMINI_MODEL, temperature=0.0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents")
def list_documents():
    """Return the list of available PDF document names (without extension)."""
    pdf_files = discover_pdf_files(DEFAULT_CORPUS_DIR)
    return [
        {"filename": p.name, "stem": p.stem}
        for p in pdf_files
    ]


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    detected_language = detect_language(request.query)
    language, translated_query = translate_query_to_english(request.query, model_name=DEFAULT_GEMINI_MODEL)
    retriever = _retriever()
    documents = retriever.invoke(translated_query)
    if not documents:
        raise HTTPException(status_code=404, detail="No supporting context found in the documents.")
    answer_en = answer_question(_chat_model(), translated_query, documents)
    answer = translate_answer_from_english(answer_en, detected_language, model_name=DEFAULT_GEMINI_MODEL) if detected_language != "en" else answer_en
    citations = [
        Citation(
            source_file=doc.metadata.get("source_file"),
            document_page_number=doc.metadata.get("document_page_number"),
            chunk_id=doc.metadata.get("chunk_id"),
            snippet=doc.page_content,
        )
        for doc in documents[:4]
    ]
    return AskResponse(answer=answer, detected_language=detected_language, translated_query=translated_query if detected_language != "en" else None, citations=citations)


@app.post("/contradict", response_model=ContradictResponse)
def contradict(request: ContradictRequest):
    result = contradict_documents(request.document_a, request.document_b, request.topic, model_name=DEFAULT_GEMINI_MODEL)
    return ContradictResponse(document_a=request.document_a, document_b=request.document_b, topic=request.topic, result=result)
