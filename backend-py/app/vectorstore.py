"""
ChefRAG Vector Store
ChromaDB wrapper using LangChain for recipe document storage and retrieval.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR, COLLECTION_NAME

# ── Singleton instances ───────────────────────────────────────────────────────

_embeddings = None
_vectorstore = None


def get_embeddings():
    """Get or create the HuggingFace embeddings model (singleton)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_vectorstore():
    """Get or create the ChromaDB vector store (singleton)."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_PERSIST_DIR,
        )
    return _vectorstore


# ── Search ────────────────────────────────────────────────────────────────────

def search_recipes(query: str, k: int = 5, source_filter: str = None):
    """
    Search the vector store for recipes matching the query.

    Returns a list of (Document, relevance_score) tuples.
    Relevance scores are in [0, 1] where higher = more relevant.
    """
    vs = get_vectorstore()

    kwargs = {"k": k}
    if source_filter:
        kwargs["filter"] = {"source": source_filter}

    try:
        results = vs.similarity_search_with_relevance_scores(query, **kwargs)
        return results
    except Exception:
        # If the collection is empty or an error occurs, return empty list
        return []


# ── Document Management ──────────────────────────────────────────────────────

def get_indexed_documents():
    """List all unique source document names in the collection."""
    vs = get_vectorstore()
    try:
        collection = vs._collection
        all_data = collection.get()
        metadatas = all_data.get("metadatas", [])
        sources = set()
        for meta in metadatas:
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(list(sources))
    except Exception:
        return []


def delete_document(source_name: str) -> int:
    """Delete all chunks belonging to a specific source document."""
    vs = get_vectorstore()
    try:
        collection = vs._collection
        results = collection.get(where={"source": source_name})
        ids = results.get("ids", [])
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception:
        return 0


def get_collection_stats() -> dict:
    """Get basic statistics about the vector store collection."""
    vs = get_vectorstore()
    try:
        collection = vs._collection
        count = collection.count()
        sources = get_indexed_documents()
        return {
            "total_chunks": count,
            "total_documents": len(sources),
            "documents": sources,
        }
    except Exception:
        return {"total_chunks": 0, "total_documents": 0, "documents": []}
