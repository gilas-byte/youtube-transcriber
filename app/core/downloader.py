"""Everything that talks to YouTube: metadata lookup and audio extraction."""

from __future__ import annotations

import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Callable

import yt_dlp

from app.config import settings
from app.core.errors import DownloadError, InvalidURLError, VideoTooLongError
from app.db.models import VideoMeta

ProgressCallback = Callable[[float, str], None]

_VIDEO_ID_PATTERNS = (
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/watch\?(?:.*&)?v=([\w-]{11})"),
    re.compile(r"youtu\.be/([\w-]{11})"),
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/shorts/([\w-]{11})"),
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/embed/([\w-]{11})"),
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/live/([\w-]{11})"),
)

_BARE_ID = re.compile(r"^[\w-]{11}$")

_BASE_OPTS: dict = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "noprogress": True,
    "retries": 3,
    "socket_timeout": 30,
}


def extract_video_id(text: str) -> str | None:
    """Pull the 11-char YouTube id out of any common link shape."""
    candidate = (text or "").strip()
    if not candidate:
        return None
    if _BARE_ID.match(candidate):
        return candidate
    for pattern in _VIDEO_ID_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return match.group(1)
    return None


def normalize_url(text: str) -> str:
    """Validate the user input and return a canonical watch URL."""
    video_id = extract_video_id(text)
    if not video_id:
        raise InvalidURLError(
            "That does not look like a YouTube link. "
            "Paste something like https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
    return f"https://www.youtube.com/watch?v={video_id}"


def fetch_metadata(url: str) -> VideoMeta:
    """Read title/channel/duration without downloading a single byte of media."""
    canonical = normalize_url(url)
    try:
        with yt_dlp.YoutubeDL({**_BASE_OPTS, "skip_download": True}) as ydl:
            info = ydl.extract_info(canonical, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_message(str(exc))) from exc

    if info is None:
        raise DownloadError("YouTube returned no information for this video.")

    duration = info.get("duration")
    meta = VideoMeta(
        video_id=info.get("id") or extract_video_id(canonical) or "unknown",
        url=info.get("webpage_url") or canonical,
        title=(info.get("title") or "Untitled video").strip(),
        channel=info.get("uploader") or info.get("channel"),
        duration_seconds=int(duration) if duration else None,
        thumbnail_url=info.get("thumbnail"),
    )

    if info.get("is_live"):
        raise DownloadError("This is a live stream. Wait until it ends and try again.")

    limit = settings.max_duration_minutes * 60
    if meta.duration_seconds and meta.duration_seconds > limit:
        raise VideoTooLongError(
            f"Video is {meta.duration_human} long, over the "
            f"{settings.max_duration_minutes} minute limit. "
            "Raise MAX_DURATION_MINUTES in .env to allow it."
        )

    return meta


def download_audio(
    url: str,
    dest_dir: Path | None = None,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """Download the best audio-only stream, then normalise it to 16 kHz mono WAV."""
    dest = dest_dir or settings.downloads_dir
    dest.mkdir(parents=True, exist_ok=True)
    stem = uuid.uuid4().hex
    template = str(dest / f"{stem}.%(ext)s")

    def hook(status: dict) -> None:
        if not on_progress:
            return
        if status.get("status") == "downloading":
            total = status.get("total_bytes") or status.get("total_bytes_estimate") or 0
            done = status.get("downloaded_bytes") or 0
            fraction = (done / total) if total else 0.0
            on_progress(min(fraction, 0.99), "Downloading audio")
        elif status.get("status") == "finished":
            on_progress(1.0, "Audio downloaded")

    options = {
        **_BASE_OPTS,
        "format": "bestaudio/best",
        "outtmpl": template,
        "progress_hooks": [hook],
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(normalize_url(url), download=True)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_message(str(exc))) from exc

    matches = sorted(dest.glob(f"{stem}.*"))
    if not matches:
        raise DownloadError("The audio file could not be found after the download.")

    return _to_wav16k(matches[0])


def _to_wav16k(source: Path) -> Path:
    """Convert to the format Whisper likes best. Falls back to the raw file."""
    if not shutil.which("ffmpeg"):
        # faster-whisper can decode most containers on its own.
        return source

    target = source.with_suffix(".16k.wav")
    command = [
        "ffmpeg", "-nostdin", "-y", "-loglevel", "error",
        "-i", str(source),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or not target.exists():
        return source

    cleanup(source)
    return target


def cleanup(*paths: Path | None) -> None:
    """Delete temporary media, ignoring anything that is already gone."""
    for path in paths:
        if not path:
            continue
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


def _friendly_message(raw: str) -> str:
    """Translate yt-dlp's noisy output into something a human can act on."""
    lowered = raw.lower()
    if "private video" in lowered:
        return "This video is private."
    if "video unavailable" in lowered or "removed" in lowered:
        return "This video is unavailable or has been removed."
    if "age" in lowered and "confirm" in lowered:
        return "This video is age-restricted and cannot be downloaded anonymously."
    if "not available in your country" in lowered or "geo" in lowered:
        return "This video is blocked in your region."
    if "sign in" in lowered or "bot" in lowered:
        return (
            "YouTube asked for a sign-in to confirm you are not a bot. "
            "Try again in a few minutes or use a different network."
        )
    if "unable to download" in lowered or "connection" in lowered or "timed out" in lowered:
        return "Network problem while contacting YouTube. Check your connection and retry."
    return raw.replace("ERROR: ", "").strip() or "yt-dlp failed to fetch this video."
