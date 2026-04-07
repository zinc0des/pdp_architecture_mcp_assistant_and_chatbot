"""
PDP Architecture Assistant — RAG Chatbot API

FastAPI server that provides a browser-based chat UI for answering
PDP architecture questions using retrieval-augmented generation.

Endpoint: http://127.0.0.1:8003
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chunk_retriever import ChunkRetriever
from rag_engine import RAGEngine

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_HOST = os.getenv("PDP_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("PDP_API_PORT", "8003"))
KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent / "docs" / "knowledge-library" / "pdp-architecture"

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PDP Architecture Assistant",
    description="RAG-powered chatbot for PDP architecture questions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for UI
UI_DIR = Path(__file__).parent / "ui"
if UI_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")

# Initialize components
retriever = ChunkRetriever(str(KNOWLEDGE_BASE_DIR))
rag_engine = RAGEngine()

# Session storage (in-memory)
sessions: dict[str, list[dict]] = {}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: list[str]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    knowledge_base_topics: int
    model: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat UI."""
    index_path = UI_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>PDP Architecture Assistant</h1><p>UI not found. Use POST /chat</p>")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    is_ready = rag_engine.is_ready
    return HealthResponse(
        status="configured" if is_ready else "degraded",
        knowledge_base_topics=len(retriever.documents),
        model=rag_engine.model_name if is_ready else f"{rag_engine.model_name} (retrieval-only)",
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message using RAG."""
    session_id = request.session_id or str(uuid.uuid4())

    # Retrieve relevant chunks
    chunks = retriever.retrieve(request.message, top_k=5)
    context = "\n\n---\n\n".join(chunk["content"] for chunk in chunks)
    sources = list(set(chunk["source"] for chunk in chunks))

    # Get conversation history
    history = sessions.get(session_id, [])

    # Generate response
    try:
        response_text = await rag_engine.generate(
            question=request.message,
            context=context,
            history=history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}") from e

    # Update session history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": response_text})
    sessions[session_id] = history[-20:]  # Keep last 20 messages

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        sources=sources,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/reset")
async def reset_session(session_id: str):
    """Reset a chat session."""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "reset", "session_id": session_id}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
