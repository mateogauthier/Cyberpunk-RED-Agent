# Cyberpunk RED Agent Chatbot

An interactive chatbot that simulates an **Agent** from the Cyberpunk RED TTRPG universe — a pocket-sized personal computer powered by SAAI (Self-Adaptive Artificial Intelligence). The Agent responds in the tone and language of the setting, and its personality adapts over the course of a conversation. You can feed it your own lore files so it answers based on actual Cyberpunk RED canon.

## Prerequisites

*   Python 3.8+
*   [Ollama](https://ollama.com) running locally with at least one model pulled (e.g. `ollama pull llama3.2`)

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd cyberpunk-agent-bot
    ```
2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```
4.  Create a `.env` file in the project root:
    ```env
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_MODEL=llama3.2
    ```
    Change `OLLAMA_MODEL` to whichever model you have pulled in Ollama.

## Running

```bash
source venv/bin/activate
uvicorn code.api_server:app --port 8000 --reload
```

Open `http://localhost:8000` in your browser. The chat interface loads automatically.

API docs are available at `http://localhost:8000/docs`.

## Lore Folder

The `lore/` folder is where you put your own Cyberpunk RED source material. The Agent will read it and use it to inform its answers.

**Supported formats:** `.txt`, `.md`, `.pdf`

**How it works:** On startup, all files in `lore/` are loaded, chunked, and indexed using BM25 keyword search. When you send a message, the most relevant excerpts are retrieved and injected into the Agent's context before it generates a response. The Agent uses that context to give lore-accurate answers without quoting it verbatim.

**To add or update lore files** without restarting the server, call:
```
POST http://localhost:8000/lore/reload
```

**Note:** The `lore/` folder is excluded from version control. Files you place there will never be committed or pushed.

## Project Structure

```
code/
  api_server.py   — FastAPI backend (chat endpoint, lore reload, static file serving)
  agent.py        — SAAI system prompt (defines the Agent's identity and capabilities)
  llm.py          — Ollama client wrapper
  rag.py          — Document loading, chunking, and BM25 retrieval
  requirements.txt
frontend/
  index.html      — Cyberpunk RED styled chat interface (served at /)
lore/             — Drop your lore files here (gitignored)
specifications.md — Cyberpunk RED Agent lore reference used during development
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Chat interface (browser) |
| `GET` | `/status` | Server status and lore chunk count |
| `POST` | `/chat` | Send a message to the Agent |
| `POST` | `/lore/reload` | Reload lore files without restarting |

### `/chat` request body

```json
{
  "message": "Tell me about Night City.",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

`history` is optional. The client is responsible for maintaining conversation history and passing it back with each request.

---
*Developed with a healthy dose of Black ICE and bad decisions.*
