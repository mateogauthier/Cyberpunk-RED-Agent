import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agent.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id     INTEGER PRIMARY KEY CHECK (id = 1),
                handle TEXT NOT NULL DEFAULT '',
                role   TEXT NOT NULL DEFAULT '',
                bio    TEXT NOT NULL DEFAULT ''
            )
        """)
        try:
            conn.execute("ALTER TABLE profile ADD COLUMN avatar_url TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        for col in ('stat_int', 'stat_ref', 'stat_tech', 'stat_cool', 'stat_will',
                    'stat_luck', 'stat_move', 'stat_body', 'stat_emp'):
            try:
                conn.execute(f"ALTER TABLE profile ADD COLUMN {col} INTEGER NOT NULL DEFAULT 5")
            except Exception:
                pass
        try:
            conn.execute("ALTER TABLE profile ADD COLUMN humanity_current INTEGER NOT NULL DEFAULT 50")
        except Exception:
            pass
        conn.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS market_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                category    TEXT NOT NULL,
                description TEXT NOT NULL,
                price       INTEGER NOT NULL,
                seller      TEXT NOT NULL,
                district    TEXT NOT NULL,
                rarity      TEXT NOT NULL DEFAULT 'COMMON',
                condition   TEXT NOT NULL DEFAULT 'USED',
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                byline     TEXT NOT NULL,
                body       TEXT NOT NULL,
                district   TEXT NOT NULL,
                category   TEXT NOT NULL DEFAULT 'GENERAL',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gigs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                category     TEXT NOT NULL,
                fixer        TEXT NOT NULL,
                payout       INTEGER NOT NULL,
                risk         TEXT NOT NULL DEFAULT 'STREET',
                district     TEXT NOT NULL,
                description  TEXT NOT NULL,
                contact      TEXT NOT NULL,
                requirements TEXT NOT NULL DEFAULT '',
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shards (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                category     TEXT NOT NULL,
                name         TEXT NOT NULL,
                description  TEXT NOT NULL,
                extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(category, name)
            )
        """)
        conn.commit()


def get_shard_names(category: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM shards WHERE category = ? ORDER BY name",
            (category,),
        ).fetchall()
    return [r["name"] for r in rows]
