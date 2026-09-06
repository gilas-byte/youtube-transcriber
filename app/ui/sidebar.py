"""Left sidebar: Whisper model picker, options, runtime status and history."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from app.config import LANGUAGES, MODEL_NAMES, WHISPER_MODELS, settings
from app.ui import history


@dataclass
class Options:
    model: str
    language: str | None
    force_refresh: bool


def _default_model_index() -> int:
    try:
        return MODEL_NAMES.index(settings.default_model)
    except ValueError:
        return MODEL_NAMES.index("small")


def _runtime_label() -> str:
    """Ask CTranslate2 once per session which device we will run on."""
    if "runtime_label" not in st.session_state:
        from app.core import transcriber

        try:
            st.session_state.runtime_label = transcriber.describe_runtime()
        except Exception:
            st.session_state.runtime_label = "unknown"
    return st.session_state.runtime_label


def render() -> Options:
    with st.sidebar:
        st.markdown('<div class="sidebar-heading">⚙️ Settings</div>', unsafe_allow_html=True)

        model = st.selectbox(
            "Whisper model",
            MODEL_NAMES,
            index=_default_model_index(),
            key="model_name",
        )
        info = WHISPER_MODELS[model]
        st.markdown(
            f'<div class="yt-chips">'
            f'<span class="yt-chip">{info["size"]}</span>'
            f'<span class="yt-chip muted">{info["speed"]}</span>'
            f'<span class="yt-chip muted">{info["quality"]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(info["hint"])

        language_label = st.selectbox(
            "Language",
            list(LANGUAGES),
            index=0,
            key="language_label",
            help="Auto-detect works well. Force a language only if detection gets it wrong.",
        )

        force_refresh = st.toggle(
            "Force re-transcribe",
            key="force_refresh",
            help="Ignore the stored result and run Whisper again.",
        )

        st.divider()

        runtime = _runtime_label()
        indicator = "🟢" if runtime.startswith("CUDA") else "🔵"
        st.markdown('<div class="sidebar-heading">Runtime</div>', unsafe_allow_html=True)
        st.caption(f"{indicator} {runtime}")

        st.divider()
        history.render()

    return Options(
        model=model,
        language=LANGUAGES[language_label],
        force_refresh=bool(force_refresh),
    )
