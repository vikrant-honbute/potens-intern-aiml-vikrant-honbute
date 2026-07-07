from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIR = ROOT_DIR / "data" / "pdfs"
DEFAULT_ARTIFACT_DIR = ROOT_DIR / "data" / "faiss_index"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150
