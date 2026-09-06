"""Central configuration, read from environment variables with sane defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_str(key: str, default: str) -> str:
    value = os.getenv(key, "").strip()
    return value or default


def _env_path(key: str, default: Path) -> Path:
    return Path(_env_str(key, str(default))).expanduser()


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env_str(key, str(default)))
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    return _env_str(key, "yes" if default else "no").lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    db_path: Path
    models_dir: Path
    downloads_dir: Path
    device: str
    compute_type: str
    default_model: str
    beam_size: int
    use_vad: bool
    max_duration_minutes: int
    history_limit: int

    def ensure_dirs(self) -> None:
        for path in (self.db_path.parent, self.models_dir, self.downloads_dir):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings(
    db_path=_env_path("DB_PATH", BASE_DIR / "data" / "transcripts.db"),
    models_dir=_env_path("MODELS_DIR", BASE_DIR / "models"),
    downloads_dir=_env_path("DOWNLOADS_DIR", BASE_DIR / "downloads"),
    device=_env_str("WHISPER_DEVICE", "auto").lower(),
    compute_type=_env_str("WHISPER_COMPUTE_TYPE", "auto").lower(),
    default_model=_env_str("DEFAULT_MODEL", "small"),
    beam_size=_env_int("WHISPER_BEAM_SIZE", 5),
    use_vad=_env_bool("WHISPER_VAD", True),
    max_duration_minutes=_env_int("MAX_DURATION_MINUTES", 180),
    history_limit=_env_int("HISTORY_LIMIT", 50),
)


# --------------------------------------------------------------------------
# Whisper model catalogue shown in the sidebar
# --------------------------------------------------------------------------

WHISPER_MODELS: dict[str, dict[str, str]] = {
    "tiny": {
        "label": "tiny",
        "size": "~0.6 GB",
        "speed": "Fastest",
        "quality": "Basic",
        "hint": "Quick drafts and very short clips.",
    },
    "base": {
        "label": "base",
        "size": "~0.8 GB",
        "speed": "Very fast",
        "quality": "Decent",
        "hint": "Clean audio, single speaker.",
    },
    "small": {
        "label": "small",
        "size": "~1.5 GB",
        "speed": "Fast",
        "quality": "Good",
        "hint": "Balanced default for most videos.",
    },
    "medium": {
        "label": "medium",
        "size": "~3.0 GB",
        "speed": "Moderate",
        "quality": "Very good",
        "hint": "Accents, noise or technical vocabulary.",
    },
    "large-v3": {
        "label": "large-v3",
        "size": "~5.0 GB",
        "speed": "Slow",
        "quality": "Best",
        "hint": "Maximum accuracy, needs a strong GPU.",
    },
    "turbo": {
        "label": "turbo",
        "size": "~3.0 GB",
        "speed": "Very fast",
        "quality": "Excellent",
        "hint": "Large-v3 quality at a fraction of the cost.",
    },
}

MODEL_NAMES = list(WHISPER_MODELS)

# Language codes offered in the sidebar. `None` means auto-detect.
LANGUAGES: dict[str, str | None] = {
    "Auto-detect": None,
    "English": "en",
    "Portuguese": "pt",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Russian": "ru",
    "Arabic": "ar",
    "Hindi": "hi",
}
