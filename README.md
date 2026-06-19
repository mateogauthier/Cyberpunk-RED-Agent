# Cyberpunk RED Agent Chatbot

An interactive chatbot that simulates an **Agent** from the Cyberpunk RED TTRPG universe — a pocket-sized personal computer powered by SAAI (Self-Adaptive Artificial Intelligence). The Agent responds in the tone and language of the setting, adapts its personality over a conversation, and is aware of your edgerunner profile. Runs entirely locally via Ollama — no cloud LLM dependency.

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com) running locally with at least one model pulled (e.g. `ollama pull llama3.2`)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cyberpunk-agent-bot
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```
4. Create a `.env` file in the project root:
   ```env
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   OLLAMA_NUM_CTX=8192
   OLLAMA_NUM_PREDICT=-1
   LORE_MIN_SCORE=7.0
   ```
   - `OLLAMA_MODEL` — whichever model you have pulled in Ollama
   - `OLLAMA_NUM_CTX` — context window size; 8192 comfortably fits lore + a long conversation
   - `OLLAMA_NUM_PREDICT` — max response tokens; `-1` lets the model end naturally
   - `LORE_MIN_SCORE` — minimum BM25 relevance score to inject a lore chunk; raise it to be more selective, lower it to retrieve more loosely related context

## Running

```bash
source venv/bin/activate
uvicorn code.api_server:app --port 8000 --reload
```

Open `http://localhost:8000` in your browser. API docs at `http://localhost:8000/docs`.

## Features

### COMM LINK
Chat with your Agent. The interface maintains full conversation history client-side and passes it back with each request. The Agent speaks in Cyberpunk RED slang, references the Night City setting, and adapts its tone to match yours over time. If you have an Edgerunner File set up, the Agent will address you by your handle and incorporate your background into its responses.

### NIGHT CITY NET
Generate breaking news articles from Night City's public information network. Each article is produced by the LLM and covers a randomized category — corporate espionage, gang warfare, netrunner incidents, NCPD operations, cyberpsychosis outbreaks, and more. Articles are persisted in SQLite and displayed newest-first (max 10 stored).

### NIGHT MARKETS
Browse black market listings sourced through fixer contacts. Each listing is LLM-generated and covers a range of categories — weapons, vehicles, cyberware, stolen data, services, contraband, tech, and medtech — with prices that vary by category, rarity, and condition. Listings are persisted in SQLite (max 20 stored). Rarity tiers: COMMON, UNCOMMON, RARE, LEGENDARY. Condition tags: NEW, USED, HOT (stolen), SALVAGE.

### EDGERUNNER FILE
Set up your operator profile: street handle, profession (Solo, Netrunner, Fixer, etc.), bio, and an avatar image (URL-based). Profile data is stored in SQLite and injected into the Agent's system prompt on every chat request, so the Agent knows who it's talking to without asking for credentials.

## Lore Folder

The `lore/` folder is where you put your own Cyberpunk RED source material. The Agent reads it and uses it to inform its answers.

**Supported formats:** `.txt`, `.md`, `.pdf`

**How it works:** On startup, all files in `lore/` are loaded, chunked, and indexed using BM25 keyword search. When you send a message, the most relevant excerpts are retrieved and injected into the Agent's context before it generates a response. The index is cached to `.lore_cache.pkl` and invalidated automatically when files change.

**To add or update lore files** without restarting the server:
```
POST http://localhost:8000/lore/reload
```

**Note:** The `lore/` folder is excluded from version control.

## Project Structure

```
code/
  api_server.py    — FastAPI app; all API routes + static file serving
  agent.py         — System prompts: Agent persona, news generator, market generator
  llm.py           — Ollama client wrapper
  rag.py           — BM25 document loading, chunking, and retrieval
  db.py            — SQLite setup (profile, news, market_items tables)
  requirements.txt
frontend/
  index.html       — Single-page app shell with four tab panels
  css/
    style.css      — Full cyberpunk theme; responsive for mobile/tablet/desktop
  js/
    app.js         — Boot sequence and tab routing
    chat.js        — Chat message rendering and history management
    news.js        — News feed rendering and generation trigger
    market.js      — Market listings rendering and generation trigger
    profile.js     — Edgerunner file form and avatar management
    api.js         — Thin fetch wrappers for all API endpoints
    icons.js       — SVG icons for news categories and market categories
    utils.js       — Shared helpers (escHtml, delay)
data/
  agent.db         — SQLite database (auto-created on first run)
lore/              — Drop lore files here (gitignored)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server health and lore chunk count |
| `POST` | `/chat` | Send a message; returns Agent reply |
| `POST` | `/lore/reload` | Rebuild lore index without restarting |
| `GET` | `/news` | Return stored news articles (newest-first, max 10) |
| `POST` | `/news` | Generate and persist one news article |
| `GET` | `/market` | Return stored market listings (newest-first, max 20) |
| `POST` | `/market` | Generate and persist one market listing |
| `GET` | `/profile` | Return stored edgerunner profile |
| `POST` | `/profile` | Upsert edgerunner profile |

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

`history` is optional. The client manages conversation history and passes it back with each request.

---
*Developed with a healthy dose of Black ICE and bad decisions.*
