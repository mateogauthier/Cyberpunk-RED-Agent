# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A chatbot that simulates an "Agent" from the Cyberpunk RED TTRPG universe — a pocket-sized AI-driven device (SAAI). Runs entirely locally via Ollama; no cloud LLM dependency.

## Setup & Running

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
uvicorn code.api_server:app --port 8000 --reload
```

Open `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

Required `.env` (gitignored):
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_NUM_CTX=8192
OLLAMA_NUM_PREDICT=-1
LORE_MIN_SCORE=7.0
```

No test suite or linter configured.

## Architecture

### Backend (`code/`)

- **`api_server.py`** — FastAPI app. Mounts `StaticFiles` for the frontend **last** so API routes take priority. Calls `init_db()` and starts lore indexing in a daemon thread at lifespan startup.
- **`llm.py`** — Thin Ollama wrapper. Reads `OLLAMA_MODEL`/`OLLAMA_HOST`/`OLLAMA_NUM_CTX`/`OLLAMA_NUM_PREDICT` from env. When `context_chunks` are provided, prepends them to the system prompt under a `## LORE REFERENCE` header.
- **`agent.py`** — Two prompt constants: `SYSTEM_PROMPT` (Agent identity/persona) and `NEWS_PROMPT` (JSON-only news generator). Both are imported by `api_server.py`.
- **`rag.py`** — BM25 keyword search over `lore/`. Loads `.txt`, `.md`, `.pdf` files; strips markdown formatting before chunking (400-word chunks, 50-word overlap, 30-word minimum). Index is cached to `.lore_cache.pkl` and invalidated by file mtime. `LoreIndex.build()` is called in a background thread at startup; `retrieve()` is thread-safe via a lock.
- **`db.py`** — SQLite at `data/agent.db` (auto-created). Two tables:
  - `profile` — single-row enforced by `CHECK (id = 1)`, seeded with `INSERT OR IGNORE`.
  - `news` — auto-increment, capped to 10 rows (oldest deleted on each insert via a subquery DELETE).

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server health + lore chunk count |
| `POST` | `/chat` | Chat; client manages and passes back full history |
| `POST` | `/lore/reload` | Rebuild lore index without restart |
| `GET` | `/news` | Return stored news (newest-first, max 10) |
| `POST` | `/news` | Generate + persist one article, trim to 10 |
| `GET` | `/profile` | Return stored edgerunner profile |
| `POST` | `/profile` | Upsert edgerunner profile |

### LLM JSON output

`NEWS_PROMPT` asks the model for raw JSON. Two post-processing steps in `api_server.py`:
1. Strip markdown code fences if the model wraps output in ` ``` `.
2. `_fix_json_escapes()` removes invalid backslash escapes (e.g. `\'`) that some models emit — only the 8 RFC-valid JSON escape characters are kept.

### Frontend (`frontend/`)

Vanilla JS/HTML/CSS — no build step, no framework.

- **`index.html`** — Four tab panels: `#panel-chat`, `#panel-map`, `#panel-news`, `#panel-profile`.
- **`main.js`** — Tab routing uses `location.hash` (`/#chat`, `/#map`, `/#news`, `/#profile`). Hash changes are handled by a `hashchange` listener calling `activateTab()`. Profile and news are loaded from the API at boot.
- **`map.js`** — Builds the Tactical Grid accordion (district cards) entirely in JS into `#map-legend`. DISTRICTS array contains lore data for Watson, City Center, Westbrook, Heywood, Pacifica, Santo Domingo.
- **`news-icons.js`** — `CATEGORY_ICONS` object mapping 10 category strings (CORPORATE, GANG, NETRUNNER, NCPD, TRAUMA_TEAM, CYBERPSYCHO, TECH, ROGUE_AI, PROTEST, GENERAL) to inline SVG strings. **Must be loaded before `main.js`** (it is, in index.html). `renderNewsCard()` in main.js reads from this global.
- **`style.css`** — Uses CSS custom properties defined at `:root` for the full color palette (`--red`, `--cyan`, `--bg`, `--border`, etc.).

### Lore folder

`lore/` is gitignored (copyright material). Drop `.txt`, `.md`, or `.pdf` files there and call `POST /lore/reload` to reindex without restarting. The current lore set includes the official Cyberpunk RED rulebook, sourcebooks, and DLC PDFs.

## Lore / Setting Accuracy

This is set in **2045**, after the 4th Corporate War. Key constraint: **Arasaka was expelled from Night City** following the 2023 Arasaka Tower bombing — they are not a present faction in the city. Active corporate powers are Militech, Petrochem, Night Corp, and Ziggurat (the in-universe provider of the Agent device and CitiNet network).
