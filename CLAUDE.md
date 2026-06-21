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
OLLAMA_MODEL=gemma4
OLLAMA_NUM_CTX=8192
OLLAMA_NUM_PREDICT=-1
LORE_MIN_SCORE=7.0
```

`OLLAMA_MODEL=gemma4` is recommended — it has native tool calling support. `llama3.2` still works for chat and RAG but has no reliable tool calling capability.

No test suite or linter configured.

## Architecture

### Backend (`code/`)

- **`api_server.py`** — FastAPI app. Mounts `StaticFiles` for the frontend **last** so API routes take priority. Calls `init_db()` and starts lore indexing in a daemon thread at lifespan startup. Uses `json-repair` (`_repair_loads`) for all LLM JSON parsing. `_now_2045()` helper generates in-universe 2045 timestamps for all generated content.
- **`llm.py`** — Ollama wrapper with agentic tool-call loop. Accepts optional `tools` list; after each LLM response, checks `response.message.tool_calls` and executes tools via `tools.py`, appending results as `role: "tool"` messages, up to 5 rounds. Returns `response.message.content or ""` (gemma4 can return `None` content after a tool round).
- **`tools.py`** — `AGENT_TOOLS` (Ollama-format tool definitions) and `execute_tool(name, args)`. Four tools: `roll_dice`, `get_gigs`, `get_news`, `get_market`. All three DB-query tools accept an optional `district` parameter (WHERE clause filter). Only wired into the `/chat` endpoint — generation endpoints do not receive tools.
- **`agent.py`** — Prompt constants: `SYSTEM_PROMPT` (Agent identity/persona + tool awareness + IMPORTANT rule to call tools instead of answering from memory), generation prompts for news/market/gigs, and `GREETING_PROMPT`. All three generation prompts include lore constraints (active corps: Militech, Petrochem, Night Corp, Ziggurat; active gangs; Arasaka expelled note).
- **`rag.py`** — BM25 keyword search over `lore/`. Loads `.txt`, `.md`, `.pdf` files; strips markdown formatting before chunking (400-word chunks, 50-word overlap, 30-word minimum). Index is cached to `.lore_cache.pkl` and invalidated by file mtime. `LoreIndex.build()` is called in a background thread at startup; `retrieve()` is thread-safe via a lock.
- **`shards.py`** — Lore entity extraction. Runs BM25 queries per category (CORPORATION, DISTRICT, FACTION), calls the LLM once per query with 4 chunks × 1500 chars max (to stay within 8192-token context window), merges and deduplicates results by name, then upserts into the `shards` table. Validation helpers `_normalize_name`, `_is_valid_name`, `_dedup_key` reject OCR garbage and case duplicates before DB insert.
- **`db.py`** — SQLite at `data/agent.db` (auto-created). Tables:
  - `profile` — single-row enforced by `CHECK (id = 1)`, seeded with `INSERT OR IGNORE`.
  - `news` — auto-increment, capped to 10 rows (oldest deleted on each insert via subquery DELETE).
  - `market_items` — capped to 20 rows.
  - `gigs` — capped to 20 rows.
  - `shards` — `UNIQUE(category, name)`; re-extraction upserts via `ON CONFLICT DO UPDATE`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server health + lore chunk count |
| `POST` | `/chat` | Chat; client manages and passes back full history |
| `POST` | `/lore/reload` | Rebuild lore index without restart |
| `GET` | `/news` | Return stored news (newest-first, max 10) |
| `POST` | `/news` | Generate + persist one article, trim to 10 |
| `GET` | `/market` | Return stored market listings (newest-first, max 20) |
| `POST` | `/market` | Generate + persist one listing, trim to 20 |
| `GET` | `/gigs` | Return stored gig postings (newest-first, max 20) |
| `POST` | `/gigs` | Generate + persist one gig, trim to 20 |
| `GET` | `/profile` | Return stored edgerunner profile |
| `POST` | `/profile` | Upsert edgerunner profile |
| `GET` | `/shards` | Return extracted lore entities grouped by category |
| `POST` | `/shards/extract` | Run full lore extraction, upsert into SQLite, return counts |

### LLM JSON output

All generation endpoints (news, market, gigs) and the shards extractor use `json-repair` (`from json_repair import loads as _repair_loads`) to parse LLM output. This handles markdown code fences, trailing commas, missing quotes, and invalid backslash escapes that models frequently emit. The old `_fix_json_escapes()` function has been removed.

### In-universe timestamps

All generated content (news, market, gigs) uses in-universe 2045 timestamps:
```python
def _now_2045() -> str:
    return datetime.utcnow().replace(year=2045).strftime("%Y-%m-%d %H:%M:%S")
```
The timestamp is computed once and passed to both the response object and the DB insert.

### Frontend (`frontend/`)

Vanilla JS/HTML/CSS — no build step, no framework. ES modules throughout.

- **`index.html`** — Six tab panels: `#panel-chat`, `#panel-news`, `#panel-market`, `#panel-gigs`, `#panel-profile`, `#panel-shards`.
- **`app.js`** — Tab routing via `data-tab` attributes and URL hash. `VALID_TABS` set gates hash values. Imports and calls all panel init functions at boot.
- **`chat.js`** — Chat rendering, RAG debug drawer, history management.
- **`news.js`** / **`market.js`** / **`gigs.js`** — Feed rendering and generation triggers for their respective panels.
- **`profile.js`** — Edgerunner file form, stats grid (9 stats, 1–10), humanity tracker with state badges.
- **`shards.js`** — Shards tab init: folder sub-tab switching (`initSubtabs()` via `data-target`), extraction trigger, collapsible entity cards (`aria-expanded` + `hidden`), `renderSection()` per category.
- **`api.js`** — Thin `fetch` wrappers for all endpoints.
- **`icons.js`** — SVG icon maps for news, market, and gig category badges.
- **`utils.js`** — `escHtml`, `delay`.
- **`style.css`** — CSS custom properties at `:root` for the full palette. Shards tab uses `--violet` / `--violet-dark` accent. Folder sub-tabs: `margin-bottom: -1px` with `border-bottom-color: var(--bg-panel)` on active tab to break the tab bar border.

### Lore folder

`lore/` is gitignored (copyright material). Drop `.txt`, `.md`, or `.pdf` files there and call `POST /lore/reload` to reindex without restarting. The current lore set includes the official Cyberpunk RED rulebook, sourcebooks, and DLC PDFs.

## Lore / Setting Accuracy

This is set in **2045**, after the 4th Corporate War. Key constraint: **Arasaka was expelled from Night City** following the 2023 Arasaka Tower bombing — they are not a present faction in the city. Active corporate powers are Militech, Petrochem, Night Corp, and Ziggurat (the in-universe provider of the Agent device and CitiNet network). Active gangs: Maelstrom, Tyger Claws, Valentinos, Animals, 6th Street, Voodoo Boys.
