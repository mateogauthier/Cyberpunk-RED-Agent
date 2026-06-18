from __future__ import annotations
import os
import ollama


def chat(system_prompt: str, history: list[dict[str, str]], user_message: str) -> str:
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    client = ollama.Client(host=host)
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat(model=model, messages=messages)
    return response.message.content
