from __future__ import annotations

import argparse
from pathlib import Path

from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document

from .config import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CORPUS_DIR,
    DEFAULT_DENSE_TOP_K,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_ENSEMBLE_C,
    DEFAULT_FAISS_INDEX_NAME,
    DEFAULT_HYBRID_WEIGHTS,
    DEFAULT_SPARSE_TOP_K,
)
from .indexing import build_embeddings, load_faiss_index
from .ingest import build_corpus_documents


def build_dense_retriever(index_dir: Path = DEFAULT_ARTIFACT_DIR, top_k: int = DEFAULT_DENSE_TOP_K):
    embeddings = build_embeddings(model_name=DEFAULT_EMBEDDING_MODEL)
    vector_store = load_faiss_index(index_dir, embeddings)
    return vector_store.as_retriever(search_kwargs={"k": top_k})


def build_sparse_retriever(documents: list[Document], top_k: int = DEFAULT_SPARSE_TOP_K) -> BM25Retriever:
    retriever = BM25Retriever.from_documents(documents)
    retriever.k = top_k
    return retriever


def build_hybrid_retriever(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    index_dir: Path = DEFAULT_ARTIFACT_DIR,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    dense_top_k: int = DEFAULT_DENSE_TOP_K,
    sparse_top_k: int = DEFAULT_SPARSE_TOP_K,
    weights: list[float] = DEFAULT_HYBRID_WEIGHTS,
    c: int = DEFAULT_ENSEMBLE_C,
) -> EnsembleRetriever:
    documents = build_corpus_documents(
        corpus_dir=corpus_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    dense_retriever = build_dense_retriever(index_dir=index_dir, top_k=dense_top_k)
    sparse_retriever = build_sparse_retriever(documents, top_k=sparse_top_k)
    return EnsembleRetriever(
        retrievers=[dense_retriever, sparse_retriever],
        weights=weights,
        c=c,
        id_key="chunk_id",
    )


def retrieve_hybrid(query: str, retriever: EnsembleRetriever) -> list[Document]:
    return retriever.invoke(query)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the hybrid FAISS + BM25 retriever.")
    parser.add_argument("query", type=str)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--dense-top-k", type=int, default=DEFAULT_DENSE_TOP_K)
    parser.add_argument("--sparse-top-k", type=int, default=DEFAULT_SPARSE_TOP_K)
    args = parser.parse_args()

    retriever = build_hybrid_retriever(
        corpus_dir=args.corpus_dir,
        index_dir=args.index_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        dense_top_k=args.dense_top_k,
        sparse_top_k=args.sparse_top_k,
    )
    documents = retrieve_hybrid(args.query, retriever)

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        print(
            f"#{index} | {metadata.get('source_file')} | p{metadata.get('document_page_number')} | {metadata.get('chunk_id')} | {document.page_content[:180].replace(chr(10), ' | ')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
