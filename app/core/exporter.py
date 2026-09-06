"""Turn a stored transcription into a Markdown file with a safe filename."""

from __future__ import annotations

import re
import unicodedata

from app.db.models import Transcription

_INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MULTI_DASH = re.compile(r"-{2,}")
_WHITESPACE = re.compile(r"\s+")


def slugify_title(title: str, max_length: int = 120, fallback: str = "transcript") -> str:
    """Make a filename out of a video title, keeping accents but dropping junk."""
    text = unicodedata.normalize("NFKC", title or "")
    # Strip emoji and control characters, keep letters/digits/punctuation.
    text = "".join(ch for ch in text if unicodedata.category(ch) not in {"So", "Cf", "Cc"})
    text = _INVALID_FS_CHARS.sub("", text)
    text = _WHITESPACE.sub(" ", text).strip()
    text = text.replace(" ", "-")
    text = _MULTI_DASH.sub("-", text).strip("-._")
    text = text[:max_length].strip("-._")
    return text or fallback


def markdown_filename(transcription: Transcription) -> str:
    return f"{slugify_title(transcription.title)}.md"


def to_markdown(transcription: Transcription) -> str:
    """Front-matter style header plus the transcript body."""
    lines = [f"# {transcription.title}", ""]

    if transcription.channel:
        lines.append(f"**Channel:** {transcription.channel}  ")
    lines.append(f"**URL:** {transcription.video_url}  ")
    lines.append(f"**Duration:** {transcription.duration_human}  ")

    detail = f"**Model:** {transcription.whisper_model}"
    if transcription.detected_language:
        detail += f" · **Language:** {transcription.detected_language}"
    if transcription.device:
        detail += f" · **Device:** {transcription.device}"
    lines.append(detail + "  ")

    lines.append(f"**Words:** {transcription.word_count}  ")
    lines.append(f"**Transcribed:** {transcription.created_at}")
    lines.extend(["", "---", "", transcription.transcript, ""])

    return "\n".join(lines)
