"""Dataclasses shared across the app."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def format_duration(seconds: float | int | None) -> str:
    """Turn 754 into '12:34' and 4210 into '1:10:10'."""
    if not seconds or seconds < 0:
        return "--:--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


@dataclass
class VideoMeta:
    """What yt-dlp tells us about a video before any download happens."""

    video_id: str
    url: str
    title: str
    channel: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None

    @property
    def duration_human(self) -> str:
        return format_duration(self.duration_seconds)


@dataclass
class TranscriptResult:
    """Raw output of the Whisper engine."""

    text: str
    segments: list[dict[str, Any]] = field(default_factory=list)
    language: str | None = None
    language_probability: float | None = None
    audio_duration: float | None = None
    model: str = ""
    device: str = ""
    compute_type: str = ""
    processing_seconds: float = 0.0


@dataclass
class Transcription:
    """One row of the `transcriptions` table."""

    id: int | None
    video_id: str
    video_url: str
    title: str
    channel: str | None
    duration_seconds: int | None
    thumbnail_url: str | None
    whisper_model: str
    detected_language: str | None
    device: str | None
    transcript: str
    segments_json: str | None
    word_count: int
    processing_seconds: float | None
    status: str
    error_message: str | None
    created_at: str

    # -- helpers ---------------------------------------------------------

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Transcription":
        return cls(**{key: row[key] for key in row.keys()})

    @classmethod
    def build(
        cls,
        meta: VideoMeta,
        result: TranscriptResult,
        status: str = "completed",
        error_message: str | None = None,
    ) -> "Transcription":
        return cls(
            id=None,
            video_id=meta.video_id,
            video_url=meta.url,
            title=meta.title,
            channel=meta.channel,
            duration_seconds=meta.duration_seconds,
            thumbnail_url=meta.thumbnail_url,
            whisper_model=result.model,
            detected_language=result.language,
            device=result.device,
            transcript=result.text,
            segments_json=json.dumps(result.segments, ensure_ascii=False),
            word_count=len(result.text.split()),
            processing_seconds=result.processing_seconds,
            status=status,
            error_message=error_message,
            created_at=datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @property
    def segments(self) -> list[dict[str, Any]]:
        if not self.segments_json:
            return []
        try:
            return json.loads(self.segments_json)
        except json.JSONDecodeError:
            return []

    @property
    def duration_human(self) -> str:
        return format_duration(self.duration_seconds)

    @property
    def processing_human(self) -> str:
        return format_duration(self.processing_seconds)

    @property
    def speed_ratio(self) -> float | None:
        """How many times faster than real time the transcription ran."""
        if not self.duration_seconds or not self.processing_seconds:
            return None
        return self.duration_seconds / self.processing_seconds
