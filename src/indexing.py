from __future__ import annotations

import argparse
import json
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from .config import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CORPUS_DIR,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_FAISS_INDEX_NAME,
)
from .ingest import build_corpus_documents, write_chunk_manifest


def build_embeddings(model_name: str = DEFAULT_EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_faiss_index(documents, embeddings: HuggingFaceEmbeddings) -> FAISS:
    return FAISS.from_documents(documents, embeddings)


def save_faiss_index(vector_store: FAISS, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    store_path = output_dir / DEFAULT_FAISS_INDEX_NAME
    vector_store.save_local(str(store_path))
    return store_path


def load_faiss_index(index_dir: Path, embeddings: HuggingFaceEmbeddings) -> FAISS:
    store_path = index_dir / DEFAULT_FAISS_INDEX_NAME
    return FAISS.load_local(str(store_path), embeddings, allow_dangerous_deserialization=True)


def build_and_persist_index(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    output_dir: Path = DEFAULT_ARTIFACT_DIR,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> dict[str, object]:
    documents = build_corpus_documents(
        corpus_dir=corpus_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    write_chunk_manifest(documents, output_dir / "chunk_manifest.jsonl")
    embeddings = build_embeddings(model_name=model_name)
    vector_store = build_faiss_index(documents, embeddings)
    store_path = save_faiss_index(vector_store, output_dir)

    return {
        "documents": documents,
        "store_path": store_path,
        "chunks": len(documents),
        "model_name": model_name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and persist the FAISS index for SchemeSense AI.")
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--model-name", type=str, default=DEFAULT_EMBEDDING_MODEL)
    args = parser.parse_args()

    result = build_and_persist_index(
        corpus_dir=args.corpus_dir,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        model_name=args.model_name,
    )

    print(
        json.dumps(
            {
                "store_path": str(result["store_path"]),
                "chunks": result["chunks"],
                "model_name": result["model_name"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
