from __future__ import annotations
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from json_repair import loads as _repair_loads

from .agent import SYSTEM_PROMPT, NEWS_PROMPT, MARKET_PROMPT, GIG_PROMPT, GREETING_PROMPT
from .db import init_db, get_connection
from .llm import chat as llm_chat
from .rag import index as lore_index
from .shards import run_full_extraction
from .tools import AGENT_TOOLS

load_dotenv()


def _now_2045() -> str:
    return datetime.utcnow().replace(year=2045).strftime("%Y-%m-%d %H:%M:%S")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    threading.Thread(target=lore_index.build, daemon=True).start()
    yield


app = FastAPI(title="Cyberpunk RED Agent", version="0.2.0", lifespan=lifespan)


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
        "version": "0.2.0",
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
            tools=AGENT_TOOLS,
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
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = _repair_loads(text)
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    ts = _now_2045()
    article = NewsResponse(
        title=data.get("title", "UNTITLED"),
        byline=data.get("byline", "ANONYMOUS"),
        body=data.get("body", ""),
        district=data.get("district", "NIGHT CITY"),
        category=data.get("category", "GENERAL"),
        created_at=ts,
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO news (title, byline, body, district, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (article.title, article.byline, article.body, article.district, article.category, ts),
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

    try:
        data = _repair_loads(text)
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    ts = _now_2045()
    item = MarketItem(
        name=data.get("name", "UNKNOWN ITEM"),
        category=data.get("category", "TECH"),
        description=data.get("description", ""),
        price=int(data.get("price", 0)),
        seller=data.get("seller", "ANONYMOUS"),
        district=data.get("district", "NIGHT CITY"),
        rarity=data.get("rarity", "COMMON"),
        condition=data.get("condition", "USED"),
        created_at=ts,
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO market_items (name, category, description, price, seller, district, rarity, condition, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item.name, item.category, item.description, item.price,
             item.seller, item.district, item.rarity, item.condition, ts),
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

    try:
        data = _repair_loads(text)
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    ts = _now_2045()
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
        created_at=ts,
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO gigs (title, category, fixer, payout, risk, district, description, contact, requirements, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (gig.title, gig.category, gig.fixer, gig.payout, gig.risk,
             gig.district, gig.description, gig.contact, gig.requirements, ts),
        )
        conn.execute("""
            DELETE FROM gigs WHERE id NOT IN (
                SELECT id FROM gigs ORDER BY created_at DESC LIMIT 20
            )
        """)
        conn.commit()

    return gig


class ShardItem(BaseModel):
    id: int
    category: str
    name: str
    description: str
    extracted_at: str | None = None


@app.get("/shards")
def get_shards():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, category, name, description, extracted_at FROM shards ORDER BY name ASC"
        ).fetchall()
    result: dict[str, list] = {"corporations": [], "districts": [], "factions": []}
    category_map = {"CORPORATION": "corporations", "DISTRICT": "districts", "FACTION": "factions"}
    for r in rows:
        key = category_map.get(r["category"])
        if key:
            result[key].append(ShardItem(**dict(r)).model_dump())
    return result


@app.post("/shards/extract")
def extract_shards():
    if not lore_index.loaded:
        raise HTTPException(status_code=503, detail="Lore index not ready — try again in a moment")
    try:
        counts = run_full_extraction(lore_index)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Extraction error: {e}")
    return {"counts": counts}


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
