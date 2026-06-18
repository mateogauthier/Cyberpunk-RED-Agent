from __future__ import annotations
import os
import re
import logging
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

LORE_DIR = Path("lore")
CHUNK_SIZE = 400       # max words per chunk
CHUNK_OVERLAP = 50     # words of overlap between chunks
MIN_CHUNK_WORDS = 30   # discard tiny fragments
TOP_K = 4              # chunks retrieved per query


# ── DOCUMENT LOADING ─────────────────────────────────────────────────────────

def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_md(path: Path) -> str:
    # Strip markdown syntax, keep plain text
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)   # headings
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)           # bold/italic
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)                 # code
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)         # links
    return text


def _load_pdf(path: Path) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return "\n\n".join(
            page.extract_text() or "" for page in reader.pages
        )
    except Exception as e:
        logger.warning("Could not parse PDF %s: %s", path, e)
        return ""


_LOADERS = {".txt": _load_txt, ".md": _load_md, ".pdf": _load_pdf}


def _load_all_documents() -> list[tuple[str, str]]:
    """Return list of (source_label, text) for all supported files in lore/."""
    if not LORE_DIR.exists():
        return []
    docs = []
    for path in sorted(LORE_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in _LOADERS:
            loader = _LOADERS[path.suffix.lower()]
            text = loader(path).strip()
            if text:
                docs.append((path.name, text))
                logger.info("Loaded lore file: %s", path.name)
    return docs


# ── CHUNKING ─────────────────────────────────────────────────────────────────

def _chunk(source: str, text: str) -> list[dict]:
    """Split text into overlapping word-window chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        if len(chunk_words) >= MIN_CHUNK_WORDS:
            chunks.append({
                "source": source,
                "text": " ".join(chunk_words),
                "tokens": chunk_words,
            })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ── BM25 INDEX ───────────────────────────────────────────────────────────────

class LoreIndex:
    def __init__(self) -> None:
        self._chunks: list[dict] = []
        self._bm25: Optional[BM25Okapi] = None
        self._loaded = False

    def build(self) -> int:
        """Load all lore files and build the BM25 index. Returns chunk count."""
        docs = _load_all_documents()
        self._chunks = []
        for source, text in docs:
            self._chunks.extend(_chunk(source, text))

        if self._chunks:
            tokenized = [c["tokens"] for c in self._chunks]
            self._bm25 = BM25Okapi(tokenized)
        else:
            self._bm25 = None

        self._loaded = True
        logger.info("Lore index built: %d chunks from %d files", len(self._chunks), len(docs))
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[str]:
        """Return the top_k most relevant lore chunks for a query, above the score threshold."""
        if not self._bm25 or not self._chunks:
            return []
        min_score = float(os.getenv("LORE_MIN_SCORE", "7.0"))
        query_tokens = query.lower().split()
        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            if scores[i] >= min_score:
                chunk = self._chunks[i]
                results.append(f"[{chunk['source']}]\n{chunk['text']}")
        return results

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


# Module-level singleton — built once at startup
index = LoreIndex()
