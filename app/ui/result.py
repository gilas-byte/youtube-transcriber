"""The transcription panel: video card, text, and the two action buttons."""

from __future__ import annotations

import html

import streamlit as st

from app.core.exporter import markdown_filename, to_markdown
from app.db.models import Transcription
from app.ui import components


def render(transcription: Transcription, from_cache: bool = False) -> None:
    _video_card(transcription, from_cache)
    _transcript_body(transcription)
    _actions(transcription)


def _video_card(item: Transcription, from_cache: bool) -> None:
    thumbnail = (
        f'<img src="{html.escape(item.thumbnail_url)}" alt="thumbnail" />'
        if item.thumbnail_url
        else ""
    )
    meta_parts = [part for part in (item.channel, item.duration_human) if part]
    meta = html.escape(" · ".join(meta_parts))

    chips = components.chips(
        (item.whisper_model, True),
        ((item.detected_language or "").upper(), False),
        (item.device or "", False),
        (f"{item.word_count} words", False),
        (f"{item.processing_human} to process" if item.processing_seconds else "", False),
        ("from history" if from_cache else "", False),
    )

    st.markdown(
        f'<div class="yt-card">{thumbnail}<div>'
        f'<div class="title">{html.escape(item.title)}</div>'
        f'<div class="meta">{meta}</div>{chips}'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _transcript_body(item: Transcription) -> None:
    st.markdown(
        f'<div class="yt-transcript">{html.escape(item.transcript)}</div>',
        unsafe_allow_html=True,
    )


def _actions(item: Transcription) -> None:
    st.markdown("")
    copy_col, download_col = st.columns(2)

    with copy_col:
        components.copy_button(item.transcript)

    with download_col:
        st.download_button(
            "⬇️ Download .md",
            data=to_markdown(item),
            file_name=markdown_filename(item),
            mime="text/markdown",
            key=f"download_{item.id}",
        )
        st.caption(f"Saves as `{markdown_filename(item)}`")
