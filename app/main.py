"""YouTube Transcripter - Streamlit entrypoint."""

from __future__ import annotations

import html
import sys
from pathlib import Path

# Make `app.*` importable no matter how Streamlit is launched.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app.config import settings  # noqa: E402
from app.core import pipeline  # noqa: E402
from app.core.errors import TranscripterError  # noqa: E402
from app.ui import result, sidebar, styles  # noqa: E402

st.set_page_config(
    page_title="YouTube Transcripter",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state() -> None:
    defaults = {
        "current": None,
        "from_cache": False,
        "error": None,
        "confirm_clear": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def url_form() -> tuple[str, bool]:
    with st.form("transcribe_form", clear_on_submit=False, border=False):
        url_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
        url = url_col.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=…",
            label_visibility="collapsed",
        )
        submitted = button_col.form_submit_button("Transcribe", use_container_width=True)
    return url.strip(), submitted


def process(url: str, options: sidebar.Options) -> None:
    """Run the pipeline while streaming progress into the page."""
    bar = st.progress(0.0)
    status = st.empty()

    def on_progress(fraction: float, message: str) -> None:
        bar.progress(min(max(fraction, 0.0), 1.0))
        status.markdown(
            f'<div class="yt-status">{html.escape(message)}</div>',
            unsafe_allow_html=True,
        )

    try:
        job = pipeline.run(
            url,
            model_name=options.model,
            language=options.language,
            force_refresh=options.force_refresh,
            on_progress=on_progress,
        )
        st.session_state.current = job.transcription
        st.session_state.from_cache = job.from_cache
        st.session_state.error = None
    except TranscripterError as exc:
        st.session_state.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - surface anything unexpected to the user
        st.session_state.error = f"Unexpected error: {exc}"
    finally:
        bar.empty()
        status.empty()

    st.rerun()


def empty_state() -> None:
    st.markdown(
        '<div class="yt-card" style="border-left-color:#7F0000;">'
        '<div><div class="title">Nothing transcribed yet</div>'
        '<div class="meta">Paste a YouTube link above, pick a Whisper model on the left, '
        "and hit Transcribe. Past runs show up in the sidebar.</div></div></div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    styles.inject()
    settings.ensure_dirs()
    init_state()

    options = sidebar.render()

    styles.hero("YouTube Transcripter", "Paste a link. Get the words.")

    url, submitted = url_form()

    if submitted:
        if not url:
            st.session_state.error = "Paste a YouTube link first."
            st.rerun()
        process(url, options)

    if st.session_state.error:
        st.error(st.session_state.error, icon="⚠️")

    if st.session_state.current:
        result.render(st.session_state.current, st.session_state.from_cache)
    elif not st.session_state.error:
        empty_state()


main()
