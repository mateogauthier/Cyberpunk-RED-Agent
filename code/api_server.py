from __future__ import annotations
import json as _json
import re as _re
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import SYSTEM_PROMPT, NEWS_PROMPT, MARKET_PROMPT, GIG_PROMPT, GREETING_PROMPT
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


@app.middleware("http")
async def no_cache_static(request, call_next):
    response = await call_next(request)
    if request.url.path.endswith((".js", ".css")):
        response.headers["Cache-Control"] = "no-store"
    return response


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    response: str
    lore_chunks: list[str] = []


class NewsResponse(BaseModel):
    title: str
    byline: str
    body: str
    district: str
    category: str = "GENERAL"
    created_at: str | None = None


class MarketItem(BaseModel):
    name: str
    category: str
    description: str
    price: int
    seller: str
    district: str
    rarity: str = "COMMON"
    condition: str = "USED"
    created_at: str | None = None


class GigPosting(BaseModel):
    title: str
    category: str
    fixer: str
    payout: int
    risk: str = "STREET"
    district: str
    description: str
    contact: str
    requirements: str = ""
    created_at: str | None = None


class ProfileModel(BaseModel):
    handle: str = ""
    role: str = ""
    bio: str = ""
    avatar_url: str = ""
    stat_int:  int = 5
    stat_ref:  int = 5
    stat_tech: int = 5
    stat_cool: int = 5
    stat_will: int = 5
    stat_luck: int = 5
    stat_move: int = 5
    stat_body: int = 5
    stat_emp:  int = 5
    humanity_current: int = 50


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


def _build_system_prompt() -> str:
    system_prompt = SYSTEM_PROMPT
    with get_connection() as conn:
        row = conn.execute("SELECT handle, role, bio FROM profile WHERE id = 1").fetchone()
    if row and row["handle"]:
        lines = [
            "## OPERATOR ON FILE",
            f"This Agent is registered to: {row['handle']}",
        ]
        if row["role"]:
            lines.append(f"Profession: {row['role']}")
        if row["bio"]:
            lines.append(f"Background: {row['bio']}")
        lines.append(
            "You already have this operator's file. "
            "Address them by their handle. "
            "Never ask them for identification or credentials — you know who they are."
        )
        system_prompt = SYSTEM_PROMPT + "\n\n" + "\n".join(lines)
    return system_prompt


@app.get("/greeting")
def greeting():
    try:
        response = llm_chat(
            system_prompt=_build_system_prompt(),
            history=[],
            user_message=GREETING_PROMPT,
            context_chunks=None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")
    return {"greeting": response}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    context = lore_index.retrieve(req.message)
    try:
        response = llm_chat(
            system_prompt=_build_system_prompt(),
            history=history,
            user_message=req.message,
            context_chunks=context,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")
    return ChatResponse(response=response, lore_chunks=context or [])


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


@app.get("/market", response_model=list[MarketItem])
def get_market():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name, category, description, price, seller, district, rarity, condition, created_at "
            "FROM market_items ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    return [MarketItem(**dict(r)) for r in rows]


@app.post("/market", response_model=MarketItem)
def generate_market_item():
    try:
        raw = llm_chat(
            system_prompt=MARKET_PROMPT,
            history=[],
            user_message="Generate a new black market listing for the Night Markets right now.",
            context_chunks=None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    text = _fix_json_escapes(text)

    try:
        data = _json.loads(text)
    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    item = MarketItem(
        name=data.get("name", "UNKNOWN ITEM"),
        category=data.get("category", "TECH"),
        description=data.get("description", ""),
        price=int(data.get("price", 0)),
        seller=data.get("seller", "ANONYMOUS"),
        district=data.get("district", "NIGHT CITY"),
        rarity=data.get("rarity", "COMMON"),
        condition=data.get("condition", "USED"),
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO market_items (name, category, description, price, seller, district, rarity, condition) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item.name, item.category, item.description, item.price,
             item.seller, item.district, item.rarity, item.condition),
        )
        conn.execute("""
            DELETE FROM market_items WHERE id NOT IN (
                SELECT id FROM market_items ORDER BY created_at DESC LIMIT 20
            )
        """)
        conn.commit()

    return item


@app.get("/gigs", response_model=list[GigPosting])
def get_gigs():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT title, category, fixer, payout, risk, district, description, contact, requirements, created_at "
            "FROM gigs ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    return [GigPosting(**dict(r)) for r in rows]


@app.post("/gigs", response_model=GigPosting)
def generate_gig():
    try:
        raw = llm_chat(
            system_prompt=GIG_PROMPT,
            history=[],
            user_message="Generate a new gig posting for the Night City fixer board right now.",
            context_chunks=None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    text = _fix_json_escapes(text)

    try:
        data = _json.loads(text)
    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    gig = GigPosting(
        title=data.get("title", "POSTING"),
        category=data.get("category", "RECON"),
        fixer=data.get("fixer", "ANONYMOUS"),
        payout=int(data.get("payout", 0)),
        risk=data.get("risk", "STREET"),
        district=data.get("district", "NIGHT CITY"),
        description=data.get("description", ""),
        contact=data.get("contact", ""),
        requirements=data.get("requirements", ""),
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO gigs (title, category, fixer, payout, risk, district, description, contact, requirements) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (gig.title, gig.category, gig.fixer, gig.payout, gig.risk,
             gig.district, gig.description, gig.contact, gig.requirements),
        )
        conn.execute("""
            DELETE FROM gigs WHERE id NOT IN (
                SELECT id FROM gigs ORDER BY created_at DESC LIMIT 20
            )
        """)
        conn.commit()

    return gig


_PROFILE_COLS = (
    "handle, role, bio, avatar_url, "
    "stat_int, stat_ref, stat_tech, stat_cool, stat_will, "
    "stat_luck, stat_move, stat_body, stat_emp, humanity_current"
)


@app.get("/profile", response_model=ProfileModel)
def get_profile():
    with get_connection() as conn:
        row = conn.execute(f"SELECT {_PROFILE_COLS} FROM profile WHERE id = 1").fetchone()
    return ProfileModel(**dict(row))


@app.post("/profile", response_model=ProfileModel)
def save_profile(profile: ProfileModel):
    with get_connection() as conn:
        conn.execute(
            """UPDATE profile SET
               handle = ?, role = ?, bio = ?, avatar_url = ?,
               stat_int = ?, stat_ref = ?, stat_tech = ?, stat_cool = ?, stat_will = ?,
               stat_luck = ?, stat_move = ?, stat_body = ?, stat_emp = ?,
               humanity_current = ?
               WHERE id = 1""",
            (profile.handle, profile.role, profile.bio, profile.avatar_url,
             profile.stat_int, profile.stat_ref, profile.stat_tech, profile.stat_cool, profile.stat_will,
             profile.stat_luck, profile.stat_move, profile.stat_body, profile.stat_emp,
             profile.humanity_current),
        )
        conn.commit()
    return profile


# Serve frontend — mounted last so API routes take priority
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
