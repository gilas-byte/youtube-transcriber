"""Exceptions the UI knows how to display."""

from __future__ import annotations


class TranscripterError(Exception):
    """Base class for every error we raise on purpose."""


class InvalidURLError(TranscripterError):
    """The text pasted by the user is not a usable YouTube link."""


class DownloadError(TranscripterError):
    """yt-dlp could not fetch the video or its audio."""


class VideoTooLongError(TranscripterError):
    """The video exceeds MAX_DURATION_MINUTES."""


class TranscriptionError(TranscripterError):
    """Whisper failed to produce a transcript."""
