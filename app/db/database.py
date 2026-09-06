"""SQLite connection handling and schema bootstrap."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator

from app.config import settings

SCHEMA_VERSION = "1"

_INIT_LOCK = threading.Lock()
_initialized = False

#: Set to False when the local SQLite build has no FTS5 support.
FTS_ENABLED = True


SCHEMA = """
CREATE TABLE IF NOT EXISTS transcriptions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id           TEXT    NOT NULL,
    video_url          TEXT    NOT NULL,
    title              TEXT    NOT NULL,
    channel            TEXT,
    duration_seconds   INTEGER,
    thumbnail_url      TEXT,

    whisper_model      TEXT    NOT NULL,
    detected_language  TEXT,
    device             TEXT,

    transcript         TEXT    NOT NULL,
    segments_json      TEXT,
    word_count         INTEGER NOT NULL DEFAULT 0,
    processing_seconds REAL,

    status             TEXT    NOT NULL DEFAULT 'completed',
    error_message      TEXT,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_created_at ON transcriptions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_id   ON transcriptions(video_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_video_model
    ON transcriptions(video_id, whisper_model);

CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Full-text search is optional: some SQLite builds ship without FTS5.
FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS transcriptions_fts
    USING fts5(title, transcript, content='transcriptions', content_rowid='id');

CREATE TRIGGER IF NOT EXISTS transcriptions_ai AFTER INSERT ON transcriptions BEGIN
    INSERT INTO transcriptions_fts(rowid, title, transcript)
    VALUES (new.id, new.title, new.transcript);
END;

CREATE TRIGGER IF NOT EXISTS transcriptions_ad AFTER DELETE ON transcriptions BEGIN
    INSERT INTO transcriptions_fts(transcriptions_fts, rowid, title, transcript)
    VALUES ('delete', old.id, old.title, old.transcript);
END;

CREATE TRIGGER IF NOT EXISTS transcriptions_au AFTER UPDATE ON transcriptions BEGIN
    INSERT INTO transcriptions_fts(transcriptions_fts, rowid, title, transcript)
    VALUES ('delete', old.id, old.title, old.transcript);
    INSERT INTO transcriptions_fts(rowid, title, transcript)
    VALUES (new.id, new.title, new.transcript);
END;
"""


def _connect() -> sqlite3.Connection:
    settings.ensure_dirs()
    conn = sqlite3.connect(settings.db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables/indexes once per process."""
    global _initialized, FTS_ENABLED

    if _initialized:
        return

    with _INIT_LOCK:
        if _initialized:
            return

        conn = _connect()
        try:
            conn.executescript(SCHEMA)
            try:
                conn.executescript(FTS_SCHEMA)
            except sqlite3.OperationalError:
                # No FTS5 in this build: repository falls back to LIKE search.
                FTS_ENABLED = False
            conn.execute(
                "INSERT INTO schema_meta(key, value) VALUES ('version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (SCHEMA_VERSION,),
            )
            conn.commit()
        finally:
            conn.close()

        _initialized = True


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Short-lived connection with commit/rollback handling."""
    init_db()
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
