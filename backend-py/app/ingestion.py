"""
ChefRAG Document Ingestion Pipeline
Handles loading, splitting, embedding, and storing recipe documents.
Uses LangChain document loaders and text splitters.
"""

import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.vectorstore import get_vectorstore


def ingest_document(file_path: str, source_name: str) -> dict:
    """
    Ingest a document into the vector store.

    Supports PDF (.pdf) and text (.txt) files.
    The document is loaded, split into chunks, embedded, and stored in ChromaDB.

    Args:
        file_path: Path to the document file.
        source_name: Name to use as the source metadata for this document.

    Returns:
        Dict with ingestion stats: source name, chunk count, page count.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # ── Load document ─────────────────────────────────────────────────────
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in (".txt", ".text"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}. Only PDF and TXT files are supported.")

    documents = loader.load()

    # ── Set source metadata ───────────────────────────────────────────────
    for doc in documents:
        doc.metadata["source"] = source_name

    # ── Split into chunks ─────────────────────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n---\n\n", "\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    # ── Store in vector database ──────────────────────────────────────────
    if chunks:
        vs = get_vectorstore()
        vs.add_documents(chunks)

    return {
        "source": source_name,
        "chunk_count": len(chunks),
        "page_count": len(documents),
    }
