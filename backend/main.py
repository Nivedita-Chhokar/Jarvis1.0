"""
main.py — FastAPI application entry point for the Voice AI Agent.
"""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.database import init_db, get_connection
from backend.agent import chat
from backend.tools import list_todos, recall_memories, delete_todo

# ── Init DB on startup ────────────────────────────────────────
init_db()

app = FastAPI(title="Voice AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve frontend static files ───────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ── Pydantic models ───────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str = ""
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: list[str]
    todos: list[dict]
    memories: list[dict]


# ── Routes ─────────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest):
    """Main chat endpoint — processes a user message through the Gemini agent."""
    session_id = req.session_id or str(uuid.uuid4())
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = chat(session_id=session_id, user_message=req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        tool_calls=result["tool_calls"],
        todos=result["todos"],
        memories=result["memories"],
    )


@app.get("/api/todos")
async def api_list_todos(status: str = ""):
    """Get the current to-do list, optionally filtered by status."""
    return list_todos(filter_status=status)


@app.delete("/api/todos/{todo_id}")
async def api_delete_todo(todo_id: int):
    """Directly delete a to-do item by ID."""
    result = delete_todo(id=todo_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/api/memories")
async def api_list_memories(query: str = ""):
    """Get stored memories, optionally filtered by a keyword query."""
    return recall_memories(query=query)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model": "gemini-2.0-flash"}
