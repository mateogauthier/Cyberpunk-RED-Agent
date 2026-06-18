# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A chatbot that simulates an "Agent" from the Cyberpunk RED TTRPG universe — an AI-driven pocket computer with a Self-Adaptive AI (SAAI). The goal is an immersive, genre-authentic roleplay experience with distinct character personas. The project is in early scaffolding stage: documentation is established, code stubs exist but are empty.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

Run the API server:
```bash
uvicorn code.api_server:app --reload
```

No test suite or linter is configured yet.

## Architecture

**Tech stack:** Python 3.8+, FastAPI, Pydantic, python-dotenv. LLM SDK integration is planned but not yet chosen (see comment in `code/requirements.txt`).

**Planned structure:**
- `code/api_server.py` — FastAPI backend (empty stub; will expose chatbot endpoints)
- `main.py` — Primary chatbot entry point (not yet created)
- `utils/` — Helper functions, lore databases, character assets (not yet created)

**Design documents (read these before implementing features):**
- `specifications.md` — Defines what an Agent *is* in the Cyberpunk RED world: SAAI technology, capabilities (communication, data management, scheduling), and security vulnerabilities. This is the canonical reference for persona behavior.
- `agents.md` — Character profile templates: archetype, background lore, vocabulary, core motivation, tone. Two example profiles exist in git history (`df1c8d0`): "Data-Ghost" (Netrunner) and "Chrome-Heart" (Solo).

**Persona model:** Each Agent has a profile that governs its vocabulary, moral stance, and conversational tone. The chatbot must maintain consistent persona per profile. New personas are added by following the template in `agents.md`.

**Environment variables:** `python-dotenv` is included — use a `.env` file for API keys and LLM provider config (file is gitignored). See the README for the required variables.
