"""
ChefRAG Configuration
All application-wide constants and environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend-py directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "openai/gpt-oss-120b"

# ── Embedding ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── ChromaDB ──────────────────────────────────────────────────────────────────
COLLECTION_NAME = "chefrag_recipes"
CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent.parent / "chroma_data")

# ── Text Chunking ─────────────────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ── Hybrid RAG Confidence Thresholds ─────────────────────────────────────────
# ChromaDB relevance scores (cosine-based): higher = more similar
HIGH_CONFIDENCE = 0.50
MEDIUM_CONFIDENCE = 0.30

# ── File Uploads ──────────────────────────────────────────────────────────────
UPLOAD_DIR = str(Path(__file__).resolve().parent.parent / "uploads")

# ── Server ────────────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000
