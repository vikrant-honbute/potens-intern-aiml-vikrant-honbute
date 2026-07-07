from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from pathlib import Path
from typing import Any


_PAGE_LABEL_RE = re.compile(r"page\s+(\d+)\s+of\s+(\d+)", re.IGNORECASE)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def guess_document_title(source_path: Path, loader_metadata: dict[str, Any]) -> str:
    title = loader_metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return source_path.stem


def guess_document_title_from_text(text: str, source_path: Path, loader_metadata: dict[str, Any]) -> str:
    title = loader_metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title_lines: list[str] = []

    for line in lines[:8]:
        lower_line = line.lower()
        if lower_line.startswith("page ") and " of " in lower_line:
            continue
        if re.fullmatch(r"(?:table of contents|contents|acronyms|foreword|disclaimer)", lower_line):
            continue
        if len(line) > 90:
            break
        if line.isupper() and title_lines:
            break

        title_lines.append(line)
        if len(" ".join(title_lines)) > 120:
            break

    if title_lines:
        return " ".join(title_lines).strip()

    return source_path.stem


def detect_page_label(text: str) -> str | None:
    match = _PAGE_LABEL_RE.search(text)
    if not match:
        return None
    return f"Page {match.group(1)} of {match.group(2)}"


def detect_document_page_number(text: str, fallback_page_number: int) -> int:
    match = _PAGE_LABEL_RE.search(text)
    if not match:
        return fallback_page_number
    return int(match.group(1))


def guess_section_hint(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    title_block: list[str] = []
    for candidate in lines[:6]:
        lower_candidate = candidate.lower()
        if lower_candidate.startswith("page ") and " of " in lower_candidate:
            continue
        if candidate.isupper() and title_block:
            break
        if len(candidate) > 80:
            break
        if not re.search(r"[A-Za-z]", candidate):
            continue
        if re.fullmatch(r"(?:government of india|national health authority|version.*|disclaimer.*)", lower_candidate):
            continue
        title_block.append(candidate)
        if len(" ".join(title_block)) > 100:
            break

    if title_block:
        return " ".join(title_block).strip()

    return lines[0][:120]


@dataclass(slots=True)
class PageMetadata:
    source_file: str
    source_path: str
    document_title: str
    loader_page_number: int
    document_page_number: int
    total_pages: int | None
    page_label: str | None
    text_chars: int
    has_text: bool
    section_hint: str | None
    extraction_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChunkMetadata(PageMetadata):
    chunk_id: str
    chunk_index: int
    chunk_start_char: int | None
    chunk_end_char: int | None
    chunk_chars: int


def build_page_metadata(
    source_path: Path,
    loader_page_number: int,
    total_pages: int | None,
    loader_metadata: dict[str, Any],
    text: str,
    document_title: str | None = None,
) -> PageMetadata:
    cleaned_text = normalize_whitespace(text)
    page_label = detect_page_label(cleaned_text)
    document_page_number = detect_document_page_number(cleaned_text, loader_page_number)
    section_hint = guess_section_hint(cleaned_text)

    notes: list[str] = []
    if not cleaned_text:
        notes.append("empty_text_layer")
    elif len(cleaned_text) < 80:
        notes.append("low_text_density")
    if page_label is not None:
        notes.append("page_label_detected")
    if section_hint is None:
        notes.append("no_clear_section_heading")

    return PageMetadata(
        source_file=source_path.name,
        source_path=str(source_path),
        document_title=document_title or guess_document_title(source_path, loader_metadata),
        loader_page_number=loader_page_number,
        document_page_number=document_page_number,
        total_pages=total_pages,
        page_label=page_label,
        text_chars=len(cleaned_text),
        has_text=bool(cleaned_text),
        section_hint=section_hint,
        extraction_notes=tuple(notes),
    )


def build_chunk_metadata(page_metadata: PageMetadata, chunk_id: str, chunk_index: int, chunk_text: str, start_char: int | None) -> ChunkMetadata:
    end_char = None if start_char is None else start_char + len(chunk_text)
    return ChunkMetadata(
        **page_metadata.to_dict(),
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        chunk_start_char=start_char,
        chunk_end_char=end_char,
        chunk_chars=len(chunk_text),
    )
