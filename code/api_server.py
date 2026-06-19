from __future__ import annotations
import json as _json
import re as _re
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import SYSTEM_PROMPT, NEWS_PROMPT
from .db import init_db, get_connection
from .llm import chat as llm_chat
from .rag import index as lore_index

load_dotenv()

# Valid single-character JSON escape sequences per RFC 8259
_VALID_JSON_ESCAPES = set('"\\\/bfnrtu')


def _fix_json_escapes(s: str) -> str:
    """Remove backslashes before characters that are not valid JSON escape targets."""
    def _replace(m: _re.Match) -> str:
        c = m.group(1)
        return m.group(0) if c in _VALID_JSON_ESCAPES else c
    return _re.sub(r'\\(.)', _replace, s)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    threading.Thread(target=lore_index.build, daemon=True).start()
    yield


app = FastAPI(title="Cyberpunk RED Agent", version="0.1.0", lifespan=lifespan)


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    response: str


class NewsResponse(BaseModel):
    title: str
    byline: str
    body: str
    district: str
    category: str = "GENERAL"
    created_at: str | None = None


class ProfileModel(BaseModel):
    handle: str = ""
    role: str = ""
    bio: str = ""


@app.get("/status")
def status():
    return {
        "status": "online",
        "project": "Cyberpunk RED Agent",
        "version": "0.1.0",
        "lore_chunks": lore_index.chunk_count,
    }


@app.post("/lore/reload")
def reload_lore():
    count = lore_index.build()
    return {"status": "ok", "chunks_loaded": count}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    context = lore_index.retrieve(req.message)
    try:
        response = llm_chat(
            system_prompt=SYSTEM_PROMPT,
            history=history,
            user_message=req.message,
            context_chunks=context,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    return ChatResponse(response=response)


@app.get("/news", response_model=list[NewsResponse])
def get_news():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT title, byline, body, district, category, created_at FROM news "
            "ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    return [
        NewsResponse(
            title=r["title"], byline=r["byline"], body=r["body"],
            district=r["district"], category=r["category"], created_at=r["created_at"],
        )
        for r in rows
    ]


@app.post("/news", response_model=NewsResponse)
def generate_news():
    try:
        raw = llm_chat(
            system_prompt=NEWS_PROMPT,
            history=[],
            user_message="Generate a breaking news article for the Night City Net right now.",
            context_chunks=None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    text = raw.strip()
    # Strip markdown code fences that some models add despite instructions
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    # Fix invalid JSON escape sequences (e.g. \' from LLM output)
    text = _fix_json_escapes(text)

    try:
        data = _json.loads(text)
    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    article = NewsResponse(
        title=data.get("title", "UNTITLED"),
        byline=data.get("byline", "ANONYMOUS"),
        body=data.get("body", ""),
        district=data.get("district", "NIGHT CITY"),
        category=data.get("category", "GENERAL"),
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO news (title, byline, body, district, category) VALUES (?, ?, ?, ?, ?)",
            (article.title, article.byline, article.body, article.district, article.category),
        )
        conn.execute("""
            DELETE FROM news WHERE id NOT IN (
                SELECT id FROM news ORDER BY created_at DESC LIMIT 10
            )
        """)
        conn.commit()

    return article


@app.get("/profile", response_model=ProfileModel)
def get_profile():
    with get_connection() as conn:
        row = conn.execute("SELECT handle, role, bio FROM profile WHERE id = 1").fetchone()
    return ProfileModel(handle=row["handle"], role=row["role"], bio=row["bio"])


@app.post("/profile", response_model=ProfileModel)
def save_profile(profile: ProfileModel):
    with get_connection() as conn:
        conn.execute(
            "UPDATE profile SET handle = ?, role = ?, bio = ? WHERE id = 1",
            (profile.handle, profile.role, profile.bio),
        )
        conn.commit()
    return profile


# Serve frontend — mounted last so API routes take priority
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
