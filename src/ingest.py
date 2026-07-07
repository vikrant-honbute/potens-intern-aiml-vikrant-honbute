from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import DEFAULT_ARTIFACT_DIR, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_CORPUS_DIR
from .metadata import build_chunk_metadata, build_page_metadata, guess_document_title_from_text, normalize_whitespace


DEFAULT_OUTPUT_FILE = "chunk_manifest.jsonl"


def discover_pdf_files(corpus_dir: Path) -> list[Path]:
    return sorted(path for path in corpus_dir.glob("*.pdf") if path.is_file())


def load_pdf_pages(pdf_path: Path) -> list[Document]:
    loader = PyMuPDFLoader(str(pdf_path))
    return loader.load()


def resolve_document_title(pdf_path: Path, page_documents: list[Document]) -> str:
    if not page_documents:
        return pdf_path.stem

    first_page_text = normalize_whitespace(page_documents[0].page_content)
    return guess_document_title_from_text(
        text=first_page_text,
        source_path=pdf_path,
        loader_metadata=dict(page_documents[0].metadata),
    )


def build_text_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
        add_start_index=True,
    )


def build_chunk_documents(
    pdf_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    page_documents = load_pdf_pages(pdf_path)
    splitter = build_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    total_pages = len(page_documents)
    document_title = resolve_document_title(pdf_path, page_documents)
    chunk_documents: list[Document] = []

    for page_index, page_document in enumerate(page_documents, start=1):
        cleaned_text = normalize_whitespace(page_document.page_content)
        page_metadata = build_page_metadata(
            source_path=pdf_path,
            loader_page_number=page_index,
            total_pages=total_pages,
            loader_metadata=dict(page_document.metadata),
            text=cleaned_text,
            document_title=document_title,
        )

        if not cleaned_text:
            chunk_id = f"{pdf_path.stem}-p{page_index:03d}-c001"
            chunk_metadata = build_chunk_metadata(page_metadata, chunk_id=chunk_id, chunk_index=1, chunk_text="", start_char=None)
            chunk_documents.append(Document(page_content="", metadata=chunk_metadata.to_dict()))
            continue

        page_chunks = splitter.split_text(cleaned_text)
        start_cursor = 0

        for chunk_index, chunk_text in enumerate(page_chunks, start=1):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue

            chunk_start = cleaned_text.find(chunk_text, start_cursor)
            if chunk_start < 0:
                chunk_start = cleaned_text.find(chunk_text)
            chunk_end = None if chunk_start < 0 else chunk_start + len(chunk_text)
            if chunk_start >= 0:
                start_cursor = chunk_start + len(chunk_text)

            chunk_id = f"{pdf_path.stem}-p{page_index:03d}-c{chunk_index:03d}"
            chunk_metadata = build_chunk_metadata(
                page_metadata,
                chunk_id=chunk_id,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                start_char=chunk_start if chunk_start >= 0 else None,
            )
            chunk_documents.append(Document(page_content=chunk_text, metadata=chunk_metadata.to_dict()))

    return chunk_documents


def build_corpus_documents(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    documents: list[Document] = []
    for pdf_path in discover_pdf_files(corpus_dir):
        documents.extend(build_chunk_documents(pdf_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return documents


def write_chunk_manifest(documents: Iterable[Document], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        for document in documents:
            record = {
                "text": document.page_content,
                **document.metadata,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize_documents(documents: list[Document]) -> dict[str, int]:
    by_source: dict[str, int] = {}
    for document in documents:
        source_file = str(document.metadata.get("source_file", "unknown"))
        by_source[source_file] = by_source.get(source_file, 0) + 1
    return by_source


def main() -> int:
    parser = argparse.ArgumentParser(description="Build chunk manifest for the SchemeSense AI corpus.")
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    args = parser.parse_args()

    documents = build_corpus_documents(
        corpus_dir=args.corpus_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    manifest_path = args.output_dir / DEFAULT_OUTPUT_FILE
    write_chunk_manifest(documents, manifest_path)

    summary = summarize_documents(documents)
    print(json.dumps({"manifest_path": str(manifest_path), "chunk_counts": summary, "total_chunks": len(documents)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
