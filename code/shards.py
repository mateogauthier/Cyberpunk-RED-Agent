from __future__ import annotations
import hashlib
import re

from json_repair import loads as _repair_loads

from .db import get_connection
from .llm import chat as llm_chat

# ── BM25 queries per category ─────────────────────────────────────────────────
# Generic terms so BM25 finds the relevant lore sections;
# the LLM discovers entity names from the text itself.

EXTRACTION_QUERIES: dict[str, list[str]] = {
    "CORPORATION": [
        "megacorporation company corporate Night City",
        "corporation headquarters board director CEO",
        "corporate subsidiary division espionage",
        "megacorp military industrial complex",
    ],
    "DISTRICT": [
        "district neighborhood Night City map",
        "borough area zone sector population",
        "district gang territory crime",
        "Night City geography location",
    ],
    "FACTION": [
        "gang turf territory street Night City",
        "faction organization criminal underground",
        "gang warfare street violence crew",
        "nomad clan group cult organization",
    ],
}

# ── Extraction prompts ────────────────────────────────────────────────────────

_PROMPTS: dict[str, str] = {
    "CORPORATION": (
        "You are a lore archivist for the Cyberpunk RED universe. "
        "The user will provide excerpts from official Cyberpunk RED source material. "
        "Extract every megacorporation or significant company mentioned in those excerpts. "
        "Return ONLY a raw JSON array — no markdown, no preamble. "
        "Each element must be an object with exactly two keys:\n"
        "- \"name\": the corporation's canonical name\n"
        "- \"description\": 2-3 sentences summarizing what this corporation does, "
        "its role in Night City, and any notable facts from the text. "
        "If the corporation was expelled from Night City or is a historical entity, say so.\n"
        "Base descriptions strictly on the provided text — do not invent facts. "
        "Deduplicate: if the same corporation appears in multiple excerpts, merge them into one entry."
    ),
    "DISTRICT": (
        "You are a lore archivist for the Cyberpunk RED universe. "
        "The user will provide excerpts from official Cyberpunk RED source material. "
        "Extract every district, borough, or named neighborhood of Night City mentioned in those excerpts. "
        "Return ONLY a raw JSON array — no markdown, no preamble. "
        "Each element must be an object with exactly two keys:\n"
        "- \"name\": the district's canonical name\n"
        "- \"description\": 2-3 sentences describing the district's character, "
        "population, dominant factions, and what it's known for.\n"
        "Base descriptions strictly on the provided text — do not invent facts. "
        "Deduplicate: if the same district appears multiple times, merge into one entry."
    ),
    "FACTION": (
        "You are a lore archivist for the Cyberpunk RED universe. "
        "The user will provide excerpts from official Cyberpunk RED source material. "
        "Extract every gang, nomad clan, paramilitary group, or significant faction mentioned in those excerpts. "
        "Do not include megacorporations — those are a separate category. "
        "Return ONLY a raw JSON array — no markdown, no preamble. "
        "Each element must be an object with exactly two keys:\n"
        "- \"name\": the faction's canonical name\n"
        "- \"description\": 2-3 sentences describing the faction's membership, territory, "
        "methods, and what they're known for in Night City.\n"
        "Base descriptions strictly on the provided text — do not invent facts. "
        "Deduplicate: if the same faction appears multiple times, merge into one entry."
    ),
}

# Each chunk is truncated to this length before being sent to the LLM so
# multiple chunks fit comfortably within the 8192-token context window.
_CHUNK_MAX_CHARS = 1500
_CHUNKS_PER_QUERY = 4


def _chunk_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


_CJK_RE = re.compile(
    r'[⺀-⿿　-鿿豈-﫿︰-﹏]+'
)

def _normalize_name(name: str) -> str:
    """Strip CJK annotation characters, collapse whitespace, trim punctuation."""
    name = _CJK_RE.sub('', name)
    name = re.sub(r'\s+', ' ', name).strip().rstrip(".,")
    return name


def _is_valid_name(name: str) -> bool:
    """Reject obvious OCR garbage and malformed extractions."""
    if not name or len(name) < 2 or len(name) > 80:
        return False
    if "=" in name:
        return False
    # Reject if the name contains three or more consecutive non-word chars
    # (common in OCR noise like "eo Ju & Derren exo")
    if name.count(" ") > 8:
        return False
    return True


def _dedup_key(name: str) -> str:
    """Case-insensitive, punctuation-stripped key for deduplication."""
    return _normalize_name(name).lower()


def _parse_entity_list(raw: str) -> list[dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    # Strip leading non-JSON noise the model sometimes emits before the array
    bracket = text.find("[")
    if bracket > 0:
        text = text[bracket:]
    try:
        data = _repair_loads(text)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        description = str(item.get("description", "")).strip()
        if not description:
            continue
        name = _normalize_name(name)
        if not _is_valid_name(name):
            continue
        results.append({"name": name, "description": description})
    return results


def _call_llm_for_query(category: str, chunks: list[str]) -> list[dict]:
    truncated = [c[:_CHUNK_MAX_CHARS] for c in chunks]
    merged = "\n\n---\n\n".join(truncated)
    try:
        raw = llm_chat(
            system_prompt=_PROMPTS[category],
            history=[],
            user_message=merged,
            context_chunks=None,
            tools=None,
        )
    except Exception:
        return []
    return _parse_entity_list(raw)


def extract_category(category: str, lore_index) -> list[dict]:
    # Run one LLM call per BM25 query; merge and deduplicate by name.
    # This keeps each call well within the context window.
    seen_hashes: set[str] = set()
    by_name: dict[str, dict] = {}

    for query in EXTRACTION_QUERIES[category]:
        chunks = lore_index.retrieve(query, top_k=_CHUNKS_PER_QUERY)
        # Deduplicate chunks across queries
        fresh = []
        for chunk in chunks:
            h = _chunk_hash(chunk)
            if h not in seen_hashes:
                seen_hashes.add(h)
                fresh.append(chunk)
        if not fresh:
            continue
        for entity in _call_llm_for_query(category, fresh):
            key = _dedup_key(entity["name"])
            if key not in by_name:
                by_name[key] = entity

    return list(by_name.values())


def run_full_extraction(lore_index) -> dict[str, int]:
    counts: dict[str, int] = {}
    for category in EXTRACTION_QUERIES:
        entities = extract_category(category, lore_index)
        with get_connection() as conn:
            for entity in entities:
                normalized = _normalize_name(entity["name"])
                conn.execute(
                    "INSERT INTO shards (category, name, description) VALUES (?, ?, ?) "
                    "ON CONFLICT(category, name) DO UPDATE SET description = excluded.description, "
                    "extracted_at = datetime('now')",
                    (category, normalized, entity["description"]),
                )
            conn.commit()
        counts[category] = len(entities)
    return counts
