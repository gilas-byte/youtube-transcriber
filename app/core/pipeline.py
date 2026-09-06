"""Orchestrates the whole job: validate -> metadata -> download -> transcribe -> store."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.config import settings
from app.core import downloader, transcriber
from app.core.errors import TranscriptionError
from app.db import repository
from app.db.models import Transcription, VideoMeta

ProgressCallback = Callable[[float, str], None]

# How much of the progress bar each stage owns.
_METADATA_END = 0.05
_DOWNLOAD_END = 0.45
_TRANSCRIBE_END = 0.98


@dataclass
class JobResult:
    transcription: Transcription
    from_cache: bool


def _noop(_fraction: float, _message: str) -> None:
    return None


def run(
    url: str,
    model_name: str,
    language: str | None = None,
    force_refresh: bool = False,
    on_progress: ProgressCallback | None = None,
) -> JobResult:
    """Produce a transcription for `url`, reusing a stored one when possible."""
    report = on_progress or _noop
    audio_path: Path | None = None

    report(0.01, "Checking the link")
    canonical_url = downloader.normalize_url(url)
    video_id = downloader.extract_video_id(canonical_url)

    if not force_refresh and video_id:
        cached = repository.find_cached(video_id, model_name)
        if cached:
            report(1.0, "Loaded from history")
            return JobResult(transcription=cached, from_cache=True)

    report(0.02, "Reading video details")
    meta: VideoMeta = downloader.fetch_metadata(canonical_url)
    report(_METADATA_END, f"Found: {meta.title}")

    try:
        def download_progress(fraction: float, message: str) -> None:
            span = _DOWNLOAD_END - _METADATA_END
            report(_METADATA_END + fraction * span, message)

        audio_path = downloader.download_audio(
            canonical_url,
            settings.downloads_dir,
            on_progress=download_progress,
        )

        def transcribe_progress(fraction: float, message: str) -> None:
            span = _TRANSCRIBE_END - _DOWNLOAD_END
            report(_DOWNLOAD_END + fraction * span, message)

        result = transcriber.transcribe(
            audio_path,
            model_name=model_name,
            language=language,
            on_progress=transcribe_progress,
        )
    finally:
        # The audio is a means to an end: never leave it behind.
        downloader.cleanup(audio_path)

    report(0.99, "Saving to history")
    transcription = Transcription.build(meta, result)
    repository.save(transcription)

    report(1.0, "Done")
    return JobResult(transcription=transcription, from_cache=False)


def preview(url: str) -> VideoMeta:
    """Metadata only, used to show the video card before transcribing."""
    return downloader.fetch_metadata(url)
