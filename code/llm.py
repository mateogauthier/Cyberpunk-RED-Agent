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
            "## LORE REFERENCE — DATA POOL RETRIEVAL\n"
            "The following excerpts were pulled from authoritative Cyberpunk RED source material. "
            "Treat these as the actual data your search returned. "
            "Your answer MUST be grounded in this content — do not invent, contradict, or speculate beyond what is here. "
            "Translate the facts into your voice as the Agent; do not quote verbatim. "
            "If the excerpts do not contain enough to answer the question, say what you found and what is missing — "
            "never fabricate a plausible-sounding answer.\n\n"
            f"{lore_block}"
        )
    else:
        full_prompt = system_prompt

    num_ctx     = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "-1"))

    client = ollama.Client(host=host)
    messages: list[dict[str, str]] = [{"role": "system", "content": full_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat(
        model=model,
        messages=messages,
        options={"num_ctx": num_ctx, "num_predict": num_predict},
    )
    return response.message.content
