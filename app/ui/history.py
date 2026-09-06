"""The transcription history rendered inside the sidebar."""

from __future__ import annotations

import html

import streamlit as st

from app.config import settings
from app.db import repository


def render() -> None:
    st.markdown('<div class="sidebar-heading">📜 History</div>', unsafe_allow_html=True)

    search = st.text_input(
        "Search history",
        key="history_search",
        placeholder="Search title or text…",
        label_visibility="collapsed",
    )

    items = repository.list_recent(limit=settings.history_limit, search=search)

    if not items:
        message = "Nothing matches that search." if search else "No transcriptions yet."
        st.caption(message)
        return

    current = st.session_state.get("current")
    current_id = current.id if current else None

    for item in items:
        _render_card(item, is_active=item.id == current_id)

    st.markdown("")
    _render_clear_all(len(items))


def _render_card(item, is_active: bool) -> None:
    active_class = " active" if is_active else ""
    meta = " · ".join(
        part
        for part in (item.created_at[:16], item.whisper_model, item.duration_human)
        if part
    )
    st.markdown(
        f'<div class="yt-hist{active_class}">'
        f'<div class="h-title">{html.escape(item.title)}</div>'
        f'<div class="h-meta">{html.escape(meta)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    open_col, delete_col = st.columns([3, 1])
    if open_col.button("Open", key=f"open_{item.id}", type="secondary"):
        st.session_state.current = repository.get_by_id(item.id)
        st.session_state.from_cache = True
        st.session_state.error = None
        st.rerun()

    if delete_col.button("🗑", key=f"del_{item.id}", type="secondary", help="Delete"):
        repository.delete(item.id)
        if is_active:
            st.session_state.current = None
        st.rerun()


def _render_clear_all(count: int) -> None:
    if st.session_state.get("confirm_clear"):
        st.warning(f"Delete all {count} transcriptions?")
        yes_col, no_col = st.columns(2)
        if yes_col.button("Yes, delete", key="clear_yes"):
            repository.clear_all()
            st.session_state.confirm_clear = False
            st.session_state.current = None
            st.rerun()
        if no_col.button("Cancel", key="clear_no", type="secondary"):
            st.session_state.confirm_clear = False
            st.rerun()
        return

    if st.button("🗑️ Clear history", key="clear_all", type="secondary"):
        st.session_state.confirm_clear = True
        st.rerun()
