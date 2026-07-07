from __future__ import annotations

import argparse
from pathlib import Path

from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_core.documents import Document

from .config import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CORPUS_DIR,
    DEFAULT_DENSE_TOP_K,
    DEFAULT_RERANK_MODEL,
    DEFAULT_RERANK_TOP_N,
    DEFAULT_SPARSE_TOP_K,
)
from .retrieval import build_hybrid_retriever


def build_reranker(model_name: str = DEFAULT_RERANK_MODEL, top_n: int = DEFAULT_RERANK_TOP_N) -> CrossEncoderReranker:
    model = HuggingFaceCrossEncoder(model_name=model_name)
    return CrossEncoderReranker(model=model, top_n=top_n)


def build_reranked_retriever(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    index_dir: Path = DEFAULT_ARTIFACT_DIR,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    dense_top_k: int = DEFAULT_DENSE_TOP_K,
    sparse_top_k: int = DEFAULT_SPARSE_TOP_K,
    rerank_top_n: int = DEFAULT_RERANK_TOP_N,
    model_name: str = DEFAULT_RERANK_MODEL,
) -> ContextualCompressionRetriever:
    hybrid_retriever = build_hybrid_retriever(
        corpus_dir=corpus_dir,
        index_dir=index_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        dense_top_k=dense_top_k,
        sparse_top_k=sparse_top_k,
    )
    compressor = build_reranker(model_name=model_name, top_n=rerank_top_n)
    return ContextualCompressionRetriever(base_compressor=compressor, base_retriever=hybrid_retriever)


def retrieve_reranked(query: str, retriever: ContextualCompressionRetriever) -> list[Document]:
    return retriever.invoke(query)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the reranked hybrid retriever.")
    parser.add_argument("query", type=str)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--dense-top-k", type=int, default=DEFAULT_DENSE_TOP_K)
    parser.add_argument("--sparse-top-k", type=int, default=DEFAULT_SPARSE_TOP_K)
    parser.add_argument("--rerank-top-n", type=int, default=DEFAULT_RERANK_TOP_N)
    parser.add_argument("--model-name", type=str, default=DEFAULT_RERANK_MODEL)
    args = parser.parse_args()

    retriever = build_reranked_retriever(
        corpus_dir=args.corpus_dir,
        index_dir=args.index_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        dense_top_k=args.dense_top_k,
        sparse_top_k=args.sparse_top_k,
        rerank_top_n=args.rerank_top_n,
        model_name=args.model_name,
    )
    documents = retrieve_reranked(args.query, retriever)

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        print(
            f"#{index} | {metadata.get('source_file')} | p{metadata.get('document_page_number')} | {metadata.get('chunk_id')} | {document.page_content[:180].replace(chr(10), ' | ')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
