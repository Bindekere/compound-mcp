import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("compound.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id  TEXT PRIMARY KEY,
            title       TEXT,
            source_tool TEXT DEFAULT 'claude_desktop',
            status      TEXT DEFAULT 'active',
            created_at  TEXT,
            updated_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS canonical_state (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id     TEXT NOT NULL,
            goal           TEXT,
            constraints    TEXT,
            reasoning      TEXT,
            decisions      TEXT,
            open_questions TEXT,
            blockers       TEXT,
            next_action    TEXT,
            version        INTEGER DEFAULT 1,
            updated_at     TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );
        """
    )
    db.commit()
    db.close()
