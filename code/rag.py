from __future__ import annotations
import os
import re
import pickle
import logging
import threading
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    """Lowercase and strip punctuation so index and query tokens match."""
    return [w for w in re.sub(r"[^a-z0-9\s]", "", text.lower()).split() if w]

logger = logging.getLogger(__name__)

LORE_DIR   = Path("lore")
CACHE_FILE = Path(".lore_cache.pkl")
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 50
MIN_CHUNK_WORDS = 30
TOP_K = 4


# ── DOCUMENT LOADING ─────────────────────────────────────────────────────────

def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_md(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text


def _load_pdf(path: Path) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.warning("Could not parse PDF %s: %s", path, e)
        return ""


_LOADERS = {".txt": _load_txt, ".md": _load_md, ".pdf": _load_pdf}


def _load_all_documents() -> list[tuple[str, str]]:
    if not LORE_DIR.exists():
        return []
    docs = []
    for path in sorted(LORE_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in _LOADERS:
            loader = _LOADERS[path.suffix.lower()]
            text = loader(path).strip()
            if text:
                docs.append((path.name, text))
                logger.info("Loaded: %s", path.name)
    return docs


# ── CHUNKING ─────────────────────────────────────────────────────────────────

def _chunk(source: str, text: str) -> list[dict]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        if len(chunk_words) >= MIN_CHUNK_WORDS:
            chunks.append({"source": source, "text": " ".join(chunk_words), "tokens": _tokenize(" ".join(chunk_words))})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ── CACHE ─────────────────────────────────────────────────────────────────────

def _lore_max_mtime() -> float:
    if not LORE_DIR.exists():
        return 0.0
    return max(
        (p.stat().st_mtime for p in LORE_DIR.rglob("*")
         if p.is_file() and p.suffix.lower() in _LOADERS),
        default=0.0,
    )


def _cache_valid() -> bool:
    return CACHE_FILE.exists() and CACHE_FILE.stat().st_mtime > _lore_max_mtime()


def _load_cache():
    try:
        with CACHE_FILE.open("rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.warning("Cache load failed: %s", e)
        return None


def _save_cache(chunks: list[dict], bm25: BM25Okapi) -> None:
    try:
        with CACHE_FILE.open("wb") as f:
            pickle.dump((chunks, bm25), f)
        logger.info("Lore cache saved to %s", CACHE_FILE)
    except Exception as e:
        logger.warning("Cache save failed: %s", e)


# ── BM25 INDEX ───────────────────────────────────────────────────────────────

class LoreIndex:
    def __init__(self) -> None:
        self._chunks: list[dict] = []
        self._bm25: Optional[BM25Okapi] = None
        self._loaded = False
        self._lock = threading.Lock()

    def build(self) -> int:
        if _cache_valid():
            result = _load_cache()
            if result is not None:
                chunks, bm25 = result
                with self._lock:
                    self._chunks, self._bm25, self._loaded = chunks, bm25, True
                logger.info("Lore index loaded from cache: %d chunks", len(chunks))
                return len(chunks)

        logger.info("Building lore index from source files (this may take a while)...")
        docs = _load_all_documents()
        chunks: list[dict] = []
        for source, text in docs:
            chunks.extend(_chunk(source, text))

        bm25 = BM25Okapi([c["tokens"] for c in chunks]) if chunks else None
        if bm25:
            _save_cache(chunks, bm25)

        with self._lock:
            self._chunks, self._bm25, self._loaded = chunks, bm25, True

        logger.info("Lore index built: %d chunks from %d files", len(chunks), len(docs))
        return len(chunks)

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[str]:
        with self._lock:
            bm25, chunks = self._bm25, self._chunks
        if not bm25 or not chunks:
            return []
        min_score = float(os.getenv("LORE_MIN_SCORE", "7.0"))
        scores = bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            if scores[i] >= min_score:
                results.append(f"[{chunks[i]['source']}]\n{chunks[i]['text']}")
        return results

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


index = LoreIndex()
