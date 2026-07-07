from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIR = ROOT_DIR / "data" / "pdfs"
DEFAULT_ARTIFACT_DIR = ROOT_DIR / "data" / "faiss_index"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_FAISS_INDEX_NAME = "faiss_store"
DEFAULT_DENSE_TOP_K = 12
DEFAULT_SPARSE_TOP_K = 12
DEFAULT_HYBRID_WEIGHTS = [0.6, 0.4]
DEFAULT_ENSEMBLE_C = 60
DEFAULT_RERANK_TOP_N = 4
DEFAULT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
