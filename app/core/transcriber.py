"""Whisper transcription through faster-whisper (CTranslate2)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from app.config import WHISPER_MODELS, settings
from app.core.errors import TranscriptionError
from app.db.models import TranscriptResult

ProgressCallback = Callable[[float, str], None]

# Loaded models stay in memory (and in VRAM) between Streamlit reruns.
_MODEL_CACHE: dict[tuple[str, str, str], object] = {}
_LOCK = threading.Lock()


def cuda_available() -> bool:
    """True when CTranslate2 can see at least one usable GPU."""
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def resolve_runtime() -> tuple[str, str]:
    """Decide which device and precision to use, honouring the .env preference."""
    device = settings.device
    if device == "auto":
        device = "cuda" if cuda_available() else "cpu"
    elif device == "cuda" and not cuda_available():
        device = "cpu"

    compute_type = settings.compute_type
    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"

    return device, compute_type


def describe_runtime() -> str:
    device, compute_type = resolve_runtime()
    label = "CUDA (GPU)" if device == "cuda" else "CPU"
    return f"{label} · {compute_type}"


def load_model(model_name: str, on_progress: ProgressCallback | None = None):
    """Return a cached WhisperModel, downloading it on first use."""
    if model_name not in WHISPER_MODELS:
        raise TranscriptionError(f"Unknown Whisper model: {model_name}")

    device, compute_type = resolve_runtime()
    key = (model_name, device, compute_type)

    with _LOCK:
        cached = _MODEL_CACHE.get(key)
        if cached is not None:
            return cached, device, compute_type

        from faster_whisper import WhisperModel

        if on_progress:
            on_progress(0.0, f"Loading model '{model_name}' (first run downloads it)")

        settings.models_dir.mkdir(parents=True, exist_ok=True)
        try:
            model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=str(settings.models_dir),
            )
        except Exception as exc:
            if device != "cuda":
                raise TranscriptionError(f"Could not load model '{model_name}': {exc}") from exc

            # Out of VRAM or a broken CUDA setup: degrade to CPU instead of failing.
            device, compute_type = "cpu", "int8"
            key = (model_name, device, compute_type)
            if on_progress:
                on_progress(0.0, "GPU unavailable, falling back to CPU")
            try:
                model = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                    download_root=str(settings.models_dir),
                )
            except Exception as cpu_exc:
                raise TranscriptionError(
                    f"Could not load model '{model_name}' on GPU or CPU: {cpu_exc}"
                ) from cpu_exc

        _MODEL_CACHE[key] = model
        return model, device, compute_type


def transcribe(
    audio_path: Path,
    model_name: str,
    language: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> TranscriptResult:
    """Run Whisper over an audio file and return the plain text plus metadata."""
    if not Path(audio_path).exists():
        raise TranscriptionError("The audio file to transcribe no longer exists.")

    started = time.perf_counter()
    model, device, compute_type = load_model(model_name, on_progress)

    try:
        segment_iter, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=settings.beam_size,
            vad_filter=settings.use_vad,
            condition_on_previous_text=False,
        )
    except Exception as exc:
        raise TranscriptionError(f"Whisper failed to start: {exc}") from exc

    total_seconds = getattr(info, "duration", 0) or 0
    pieces: list[str] = []
    segments: list[dict] = []

    try:
        for segment in segment_iter:
            text = (segment.text or "").strip()
            if text:
                pieces.append(text)
            segments.append(
                {
                    "start": round(float(segment.start), 3),
                    "end": round(float(segment.end), 3),
                    "text": text,
                }
            )
            if on_progress and total_seconds:
                fraction = min(float(segment.end) / total_seconds, 0.99)
                on_progress(fraction, "Transcribing")
    except Exception as exc:
        raise TranscriptionError(f"Whisper stopped mid-way: {exc}") from exc

    if on_progress:
        on_progress(1.0, "Transcription complete")

    text = " ".join(pieces).strip()
    if not text:
        raise TranscriptionError(
            "No speech was detected in this video. "
            "It may be music-only, silent, or the wrong language was forced."
        )

    return TranscriptResult(
        text=text,
        segments=segments,
        language=getattr(info, "language", None),
        language_probability=getattr(info, "language_probability", None),
        audio_duration=total_seconds or None,
        model=model_name,
        device=device,
        compute_type=compute_type,
        processing_seconds=round(time.perf_counter() - started, 2),
    )


def loaded_models() -> list[str]:
    with _LOCK:
        return sorted({key[0] for key in _MODEL_CACHE})


def unload_models() -> None:
    """Drop cached models to free RAM/VRAM."""
    with _LOCK:
        _MODEL_CACHE.clear()
