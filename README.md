---
title: SchemeSense AI
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app_streamlit.py
pinned: false
---

# SchemeSense AI — Document Q&A with Citations

A Retrieval-Augmented Generation (RAG) system for Indian government scheme documents that provides grounded answers with citations and contradiction detection across documents.

---

## Architecture Overview

```
User Query
    │
    ▼
┌────────────────────┐
│  Language Detection │  (langdetect)
│  + Translation      │  (Gemini LLM)
└────────┬───────────┘
         ▼
┌────────────────────┐
│  Hybrid Retrieval   │
│  ┌──────┐ ┌──────┐ │
│  │FAISS │ │BM25  │ │  Dense (semantic) + Sparse (keyword)
│  │Dense │ │Sparse│ │  combined via EnsembleRetriever
│  └──┬───┘ └──┬───┘ │  weights: [0.6, 0.4]
│     └───┬────┘     │
│         ▼          │
│  ┌──────────────┐  │
│  │  CrossEncoder │  │  ms-marco-MiniLM-L-6-v2 reranker
│  │  Reranker     │  │  top_n=4
│  └──────────────┘  │
└────────┬───────────┘
         ▼
┌────────────────────┐
│  Gemini LLM         │  gemini-2.5-flash
│  (Grounded Answer)  │  System prompt enforces no-hallucination
└────────┬───────────┘
         ▼
┌────────────────────┐
│  Answer + Citations  │  source_file, page, chunk_id, snippet
│  + Translation       │  back to user's language
└────────────────────┘
```

---

## Chunking Strategy

### Why This Strategy

Government scheme documents contain dense legalese with interconnected clauses. The chunking strategy is designed to:

1. **Preserve semantic boundaries** — not split mid-sentence or mid-paragraph
2. **Maintain enough context** for the LLM to reason about eligibility criteria, amounts, and procedures
3. **Keep chunks small enough** for precise retrieval — avoiding the "lost in the middle" problem

### Implementation Details

| Parameter         | Value                            | Rationale                                                                                             |
| ----------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `chunk_size`      | 1200 chars                       | ~200-250 words — large enough to hold a complete policy clause but small enough for precise retrieval |
| `chunk_overlap`   | 150 chars                        | ~1-2 sentences of overlap to prevent information loss at chunk boundaries                             |
| Splitter          | `RecursiveCharacterTextSplitter` | Tries `\n\n` → `\n` → `. ` → ` ` → `""` in order, preserving natural document structure               |
| `add_start_index` | `True`                           | Tracks character offset for precise citation back to original page                                    |

### Chunking Pipeline

1. **PDF Loading** — `PyMuPDFLoader` extracts text per page with layout preservation
2. **Whitespace Normalization** — Collapses non-breaking spaces, `\r\n`, and redundant blank lines
3. **Per-Page Splitting** — Each page is chunked independently to maintain page-level citation accuracy
4. **Metadata Enrichment** — Each chunk gets:
   - `source_file`, `document_title`, `document_page_number`
   - `chunk_id` (e.g., `PM-KISSAN FAQ-p003-c002`)
   - `chunk_start_char`, `chunk_end_char` for exact location
   - `section_hint` — auto-detected section heading
   - `extraction_notes` — quality flags (empty text, low density, etc.)

---

## Corpus

8 substantive Indian government scheme documents (PDFs):

| Document                                | Focus Area                         |
| --------------------------------------- | ---------------------------------- |
| PM-KISAN FAQ                            | Farmer income support Q&A          |
| Revised PM-KISAN Operational Guidelines | Eligibility, verification, payment |
| PM Vishwakarma Guidelines               | Artisan/craftsperson support       |
| PM Vishwakarma Scheme                   | Scheme overview                    |
| PM-JAY Operational Guidelines           | Health insurance (Ayushman Bharat) |
| Pradhan Mantri Mudra Yojana             | Micro-enterprise loans             |
| Stand Up India Scheme                   | SC/ST/Women entrepreneur loans     |
| Guidelines for PM Arogya Mitra          | Health scheme facilitators         |

---

## API Endpoints

### `GET /health`

Health check. Returns `{"status": "ok"}`.

### `POST /ask`

Ask a question and receive a grounded answer with citations.

**Request:**

```json
{
  "query": "What is the eligibility for PM-KISAN?"
}
```

**Response:**

```json
{
  "answer": "The PM-KISAN scheme covers ...",
  "detected_language": "en",
  "translated_query": null,
  "citations": [
    {
      "source_file": "PM-KISSAN FAQ.pdf",
      "document_page_number": 3,
      "chunk_id": "PM-KISSAN FAQ-p003-c001",
      "snippet": "All land holding eligible farmer families ..."
    }
  ]
}
```

**No-hallucination guarantee:** If the documents don't cover the question, the system explicitly says _"The documents do not cover this question."_

### `POST /contradict`

Check if two documents conflict on a given topic.

**Request:**

```json
{
  "document_a": "PM-KISSAN FAQ",
  "document_b": "RevisedPM-KISANOperationalGuidelines(English)",
  "topic": "eligibility"
}
```

**Response:**

```json
{
  "document_a": "PM-KISSAN FAQ",
  "document_b": "RevisedPM-KISANOperationalGuidelines(English)",
  "topic": "eligibility",
  "result": "No conflict found. Both documents consistently state ..."
}
```

---

## Multilingual Flow

1. **Detection** — `langdetect` identifies the query language
2. **Translation to English** — If non-English, Gemini translates the query
3. **Retrieval + Answer** — Performed in English for best embedding/retrieval quality
4. **Translation back** — Answer is translated to the user's original language

Supports Hindi, Marathi, Tamil, Telugu, Bengali, and any language Gemini can handle.

---

## Retrieval Pipeline

### Stage 1: Hybrid Retrieval

- **Dense (FAISS)** — `all-MiniLM-L6-v2` embeddings, top-12 candidates
- **Sparse (BM25)** — Keyword matching, top-12 candidates
- **Ensemble** — Reciprocal Rank Fusion with weights `[0.6 dense, 0.4 sparse]`, `c=60`

### Stage 2: Reranking

- **Cross-encoder** — `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Re-scores the ~22 hybrid candidates and returns top-4

---

## Tech Stack

| Component          | Technology                               |
| ------------------ | ---------------------------------------- |
| Vector Store       | FAISS (CPU)                              |
| Embeddings         | `sentence-transformers/all-MiniLM-L6-v2` |
| Reranker           | `cross-encoder/ms-marco-MiniLM-L-6-v2`   |
| LLM                | Google Gemini 2.5 Flash (free tier)      |
| Sparse Retrieval   | BM25 via `rank-bm25`                     |
| PDF Parsing        | PyMuPDF                                  |
| API                | FastAPI + Uvicorn                        |
| UI                 | Streamlit                                |
| Language Detection | `langdetect`                             |

---

## Setup & Run

### Prerequisites

- Python 3.10+
- A Gemini API key ([get one free](https://aistudio.google.com/app/apikey))

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd potens-intern-aiml-vikrant-honbute

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY and GOOGLE_API_KEY
```

### Build the Index

```bash
python -m src.indexing
```

### Run

```bash
# Start the FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000

# In another terminal, start Streamlit
streamlit run app_streamlit.py --server.port 7860
```

Or use the start script (Linux/Docker):

```bash
bash start.sh
```

### Docker

```bash
docker build -t schemesense-ai .
docker run -p 7860:7860 --env-file .env schemesense-ai
```

---

## Project Structure

```
├── api/
│   ├── __init__.py
│   └── main.py              # FastAPI endpoints (/ask, /contradict)
├── src/
│   ├── config.py             # Constants, paths, model names
│   ├── ingest.py             # PDF loading, chunking, manifest
│   ├── metadata.py           # Rich metadata extraction per chunk
│   ├── indexing.py           # FAISS index build & load
│   ├── retrieval.py          # Dense + BM25 hybrid retriever
│   ├── rerank.py             # Cross-encoder reranking
│   ├── llm.py                # Gemini LLM integration
│   ├── contradict.py         # Document contradiction detection
│   └── translate.py          # Multilingual query/answer translation
├── data/
│   ├── pdfs/                 # Source PDF documents
│   └── faiss_index/          # Persisted FAISS index + manifest
├── app_streamlit.py          # Streamlit UI
├── requirements.txt
├── Dockerfile
├── start.sh
└── .env.example
```

---

## AI Use Log

I used GitHub Copilot with GPT-5.4 mini while building this project. I used it as a coding assistant to speed up scaffolding, write repetitive boilerplate, shape the ingestion and retrieval pipeline, and draft the README structure. I still understood the whole project myself, chose the architecture, selected the documents, validated the chunking strategy, checked the retrieval behavior, and tested the app locally before moving to the next step.

I also used Claude for planning, strategy, and advice on how to build the project cleanly. That helped me think through the build order, the tradeoffs in the retrieval pipeline, and how to present the work honestly in the README. I treated that guidance as support, not as a replacement for my own decisions.

I also used AI to help me debug import issues, refine metadata extraction for messy PDFs, tune the retrieval pipeline, and quickly rewrite parts of the documentation in a clearer submission style. I reviewed every generated piece carefully and adjusted the code where needed so the final project reflects my own understanding and decisions.

In short: I did use AI to build this project, but I did not treat it as a black box. I used it to move faster, while I kept control over the design, the implementation choices, and the final validation.
