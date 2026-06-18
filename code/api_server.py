from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import SYSTEM_PROMPT
from .llm import chat as llm_chat
from .rag import index as lore_index

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    lore_index.build()
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


# Serve frontend — mounted last so API routes take priority
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
