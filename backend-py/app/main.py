"""
ChefRAG — Intelligent Recipe RAG Agent
FastAPI application entry point.

Provides endpoints for:
- Document upload and indexing
- Conversational Q&A with multi-agent routing
- Document management (list, delete)
- Session history management
"""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from app.config import UPLOAD_DIR, PORT, HOST
from app.ingestion import ingest_document
from app.vectorstore import get_indexed_documents, delete_document, get_collection_stats
from app.agents.orchestrator import run_agent, clear_history


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="ChefRAG",
    description="Intelligent Recipe RAG Agent — Multi-agent system for recipe search, adaptation, and cooking guidance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Request/Response Models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's question or request")
    session_id: Optional[str] = Field("default", description="Session ID for conversation history")
    preferences: Optional[dict] = Field(None, description="User preferences dict with keys: dietary_restrictions, cuisine_preference, available_ingredients, max_cooking_time")


class ChatResponse(BaseModel):
    answer: str


class UploadResponse(BaseModel):
    message: str
    source: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[str]


class StatsResponse(BaseModel):
    total_chunks: int
    total_documents: int
    documents: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/upload", response_model=UploadResponse)
async def upload_document(document: UploadFile = File(...)):
    """
    Upload and index a recipe document (PDF or TXT).

    The document is parsed, split into chunks, embedded using HuggingFace
    all-MiniLM-L6-v2, and stored in the ChromaDB vector store.
    """
    if not document.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(document.filename).suffix.lower()
    if ext not in (".pdf", ".txt", ".text"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and TXT files are supported."
        )

    file_path = os.path.join(UPLOAD_DIR, document.filename)

    try:
        # Save uploaded file temporarily
        with open(file_path, "wb") as f:
            shutil.copyfileobj(document.file, f)

        # Ingest into vector store
        result = ingest_document(file_path, document.filename)

        return UploadResponse(
            message=f"'{document.filename}' uploaded and indexed successfully!",
            source=result["source"],
            chunk_count=result["chunk_count"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Conversational Q&A with the multi-agent recipe assistant.

    The orchestrator agent analyzes the query, routes it to the appropriate
    sub-agent (retrieval, adaptation, nutrition, or shopping list), and
    returns a comprehensive, formatted answer.

    Unlike the previous system, this will NEVER say "I don't have enough
    information" — it uses a hybrid RAG strategy that blends document
    context with LLM culinary knowledge.
    """
    try:
        answer = run_agent(
            query=request.question,
            session_id=request.session_id or "default",
            preferences=request.preferences,
        )
        return ChatResponse(answer=answer)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all indexed recipe documents."""
    try:
        docs = get_indexed_documents()
        return DocumentListResponse(documents=docs)
    except Exception:
        return DocumentListResponse(documents=[])


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics."""
    stats = get_collection_stats()
    return StatsResponse(**stats)


@app.delete("/documents/{source_name}")
async def remove_document(source_name: str):
    """Remove a document and all its chunks from the index."""
    try:
        count = delete_document(source_name)
        if count == 0:
            raise HTTPException(status_code=404, detail=f"Document '{source_name}' not found")
        return {"message": f"Removed {count} chunks for '{source_name}'"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-history")
async def clear_chat_history(session_id: str = "default"):
    """Clear conversation history for a session."""
    clear_history(session_id)
    return {"message": "Conversation history cleared"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ChefRAG"}


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
