from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import SYSTEM_PROMPT
from .llm import chat as llm_chat

load_dotenv()

app = FastAPI(title="Cyberpunk RED Agent", version="0.1.0")


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    response: str


@app.get("/")
def root():
    return {"status": "online", "project": "Cyberpunk RED Agent", "version": "0.1.0"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    try:
        response = llm_chat(
            system_prompt=SYSTEM_PROMPT,
            history=history,
            user_message=req.message,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    return ChatResponse(response=response)
