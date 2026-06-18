from __future__ import annotations
import os
import ollama


def chat(
    system_prompt: str,
    history: list[dict[str, str]],
    user_message: str,
    context_chunks: list[str] | None = None,
) -> str:
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    if context_chunks:
        lore_block = "\n\n---\n\n".join(context_chunks)
        full_prompt = (
            f"{system_prompt}\n\n"
            "## LORE REFERENCE\n"
            "The following excerpts are from authoritative Cyberpunk RED lore sources. "
            "Use them to inform your response. Do not quote them verbatim — speak as the Agent would.\n\n"
            f"{lore_block}"
        )
    else:
        full_prompt = system_prompt

    client = ollama.Client(host=host)
    messages: list[dict[str, str]] = [{"role": "system", "content": full_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat(model=model, messages=messages)
    return response.message.content
