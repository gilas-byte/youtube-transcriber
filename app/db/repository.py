"""All reads and writes against the transcriptions table."""

from __future__ import annotations

from typing import Any

from app.db import database
from app.db.database import get_connection
from app.db.models import Transcription

_COLUMNS = (
    "video_id, video_url, title, channel, duration_seconds, thumbnail_url, "
    "whisper_model, detected_language, device, transcript, segments_json, "
    "word_count, processing_seconds, status, error_message, created_at"
)
_PLACEHOLDERS = ", ".join("?" * len(_COLUMNS.split(",")))


def save(item: Transcription) -> int:
    """Insert a transcription, or overwrite the previous run of the same video+model."""
    values = (
        item.video_id,
        item.video_url,
        item.title,
        item.channel,
        item.duration_seconds,
        item.thumbnail_url,
        item.whisper_model,
        item.detected_language,
        item.device,
        item.transcript,
        item.segments_json,
        item.word_count,
        item.processing_seconds,
        item.status,
        item.error_message,
        item.created_at,
    )
    sql = f"""
        INSERT INTO transcriptions ({_COLUMNS})
        VALUES ({_PLACEHOLDERS})
        ON CONFLICT(video_id, whisper_model) DO UPDATE SET
            video_url          = excluded.video_url,
            title              = excluded.title,
            channel            = excluded.channel,
            duration_seconds   = excluded.duration_seconds,
            thumbnail_url      = excluded.thumbnail_url,
            detected_language  = excluded.detected_language,
            device             = excluded.device,
            transcript         = excluded.transcript,
            segments_json      = excluded.segments_json,
            word_count         = excluded.word_count,
            processing_seconds = excluded.processing_seconds,
            status             = excluded.status,
            error_message      = excluded.error_message,
            created_at         = excluded.created_at
        RETURNING id
    """
    with get_connection() as conn:
        row = conn.execute(sql, values).fetchone()
        item.id = int(row["id"])
        return item.id


def get_by_id(item_id: int) -> Transcription | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM transcriptions WHERE id = ?", (item_id,)).fetchone()
    return Transcription.from_row(row) if row else None


def find_cached(video_id: str, whisper_model: str) -> Transcription | None:
    """Look for a successful run of this exact video with this exact model."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM transcriptions "
            "WHERE video_id = ? AND whisper_model = ? AND status = 'completed'",
            (video_id, whisper_model),
        ).fetchone()
    return Transcription.from_row(row) if row else None


def list_recent(limit: int = 50, search: str | None = None) -> list[Transcription]:
    query = (search or "").strip()
    with get_connection() as conn:
        if not query:
            rows = conn.execute(
                "SELECT * FROM transcriptions ORDER BY datetime(created_at) DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        elif database.FTS_ENABLED:
            try:
                rows = conn.execute(
                    "SELECT t.* FROM transcriptions_fts f "
                    "JOIN transcriptions t ON t.id = f.rowid "
                    "WHERE transcriptions_fts MATCH ? "
                    "ORDER BY rank LIMIT ?",
                    (_fts_query(query), limit),
                ).fetchall()
            except Exception:
                rows = _like_search(conn, query, limit)
        else:
            rows = _like_search(conn, query, limit)
    return [Transcription.from_row(row) for row in rows]


def _fts_query(query: str) -> str:
    """Escape user input into a safe prefix query for FTS5."""
    tokens = [token.replace('"', "") for token in query.split() if token.strip()]
    return " ".join(f'"{token}"*' for token in tokens) or '""'


def _like_search(conn, query: str, limit: int) -> list[Any]:
    pattern = f"%{query}%"
    return conn.execute(
        "SELECT * FROM transcriptions WHERE title LIKE ? OR transcript LIKE ? "
        "ORDER BY datetime(created_at) DESC, id DESC LIMIT ?",
        (pattern, pattern, limit),
    ).fetchall()


def delete(item_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM transcriptions WHERE id = ?", (item_id,))


def clear_all() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM transcriptions")


def get_stats() -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(duration_seconds), 0) AS audio_seconds, "
            "COALESCE(SUM(word_count), 0) AS words "
            "FROM transcriptions WHERE status = 'completed'"
        ).fetchone()
        favourite = conn.execute(
            "SELECT whisper_model, COUNT(*) AS uses FROM transcriptions "
            "GROUP BY whisper_model ORDER BY uses DESC LIMIT 1"
        ).fetchone()
    return {
        "total": row["total"],
        "audio_seconds": row["audio_seconds"],
        "words": row["words"],
        "favourite_model": favourite["whisper_model"] if favourite else None,
    }
