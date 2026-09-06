"""The red spectrum: palette constants and the CSS injected into every page."""

from __future__ import annotations

import streamlit as st

# --- Palette -------------------------------------------------------------
CRIMSON_DEEP = "#4A0000"   # borders, shadows
BLOOD = "#7F0000"          # secondary elements
SCARLET = "#B00020"        # hover
RED_PRIMARY = "#E50914"    # buttons, main accent
RED_BRIGHT = "#FF1E1E"     # active hover, progress bar
CORAL = "#FF6B6B"          # links, icons
BLUSH = "#FFB3B3"          # secondary text
BG_DARK = "#120404"        # page background
BG_PANEL = "#1F0808"       # cards, sidebar
TEXT = "#F7E9E9"           # primary text

_CSS = """
<style>
/* ---------- Base ---------- */
.stApp,
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1100px 520px at 50% -12%, rgba(229, 9, 20, 0.16), transparent 62%),
        #120404;
    color: #F7E9E9;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.4rem; max-width: 1180px; }

/* ---------- Hero ---------- */
.yt-hero { text-align: center; margin: 0 0 2.2rem; }
.yt-hero h1 {
    font-size: 3.1rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0;
    background: linear-gradient(100deg, #7F0000 0%, #E50914 45%, #FF6B6B 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
.yt-hero p {
    color: #FFB3B3;
    font-size: 1.02rem;
    margin: 0.5rem 0 0;
    letter-spacing: 0.01em;
}
.yt-hero .rule {
    height: 2px;
    width: 190px;
    margin: 1.3rem auto 0;
    border-radius: 2px;
    background: linear-gradient(90deg, transparent, #E50914, transparent);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1F0808 0%, #150505 100%);
    border-right: 1px solid #4A0000;
}
[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
.sidebar-heading {
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #FF6B6B;
    margin: 0.2rem 0 0.7rem;
}

/* ---------- Inputs ---------- */
.stTextInput input,
.stTextArea textarea {
    background: #1A0606 !important;
    color: #F7E9E9 !important;
    border: 1px solid #4A0000 !important;
    border-radius: 10px !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #E50914 !important;
    box-shadow: 0 0 0 2px rgba(229, 9, 20, 0.25) !important;
}
.stTextInput input::placeholder { color: #8A5C5C !important; }

[data-baseweb="select"] > div {
    background: #1A0606 !important;
    border-color: #4A0000 !important;
    border-radius: 10px !important;
}
[data-baseweb="select"] > div:hover { border-color: #E50914 !important; }
[data-baseweb="popover"] li:hover { background: rgba(229, 9, 20, 0.18) !important; }

/* ---------- Buttons ---------- */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #B00020 0%, #E50914 100%);
    color: #FFFFFF;
    border: 1px solid #FF1E1E;
    border-radius: 10px;
    font-weight: 650;
    letter-spacing: 0.015em;
    padding: 0.55rem 1.1rem;
    transition: transform 0.12s ease, box-shadow 0.2s ease, filter 0.2s ease;
    width: 100%;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    filter: brightness(1.12);
    box-shadow: 0 0 22px rgba(229, 9, 20, 0.45);
    transform: translateY(-1px);
    border-color: #FF6B6B;
    color: #FFFFFF;
}
.stButton > button:active { transform: translateY(0); }
.stButton > button:focus:not(:active) { color: #FFFFFF; }

/* Secondary (ghost) buttons: history actions */
.stButton > button[kind="secondary"] {
    background: transparent;
    border: 1px solid #4A0000;
    color: #FFB3B3;
    font-weight: 550;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #E50914;
    color: #FFFFFF;
    background: rgba(229, 9, 20, 0.12);
    box-shadow: none;
}

/* ---------- Progress ---------- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #7F0000, #E50914 55%, #FF6B6B);
}
.stProgress > div > div > div { background: #2A0A0A; }
.yt-status {
    color: #FFB3B3;
    font-size: 0.88rem;
    text-align: center;
    margin-top: 0.35rem;
    letter-spacing: 0.02em;
}

/* ---------- Video card ---------- */
.yt-card {
    display: flex;
    gap: 1rem;
    align-items: center;
    background: linear-gradient(135deg, #1F0808 0%, #180606 100%);
    border: 1px solid #4A0000;
    border-left: 3px solid #E50914;
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1rem;
}
.yt-card img {
    width: 150px;
    border-radius: 8px;
    border: 1px solid #4A0000;
    flex-shrink: 0;
}
.yt-card .title {
    font-size: 1.12rem;
    font-weight: 700;
    color: #F7E9E9;
    line-height: 1.3;
    margin-bottom: 0.35rem;
}
.yt-card .meta { color: #FFB3B3; font-size: 0.85rem; }

/* ---------- Chips ---------- */
.yt-chips { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.55rem; }
.yt-chip {
    background: rgba(229, 9, 20, 0.12);
    border: 1px solid #7F0000;
    color: #FF6B6B;
    border-radius: 999px;
    padding: 0.18rem 0.65rem;
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.yt-chip.muted { color: #FFB3B3; border-color: #4A0000; background: rgba(255, 255, 255, 0.03); }

/* ---------- Transcript ---------- */
.yt-transcript {
    background: #180606;
    border: 1px solid #4A0000;
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    max-height: 480px;
    overflow-y: auto;
    color: #F0E2E2;
    line-height: 1.75;
    font-size: 0.97rem;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* ---------- History cards ---------- */
.yt-hist {
    background: #180606;
    border: 1px solid #330A0A;
    border-left: 3px solid #7F0000;
    border-radius: 8px;
    padding: 0.5rem 0.7rem;
    margin-bottom: 0.3rem;
    transition: border-color 0.18s ease;
}
.yt-hist:hover { border-left-color: #FF1E1E; }
.yt-hist .h-title {
    color: #F7E9E9;
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.25;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.yt-hist .h-meta { color: #A87878; font-size: 0.72rem; margin-top: 0.2rem; }
.yt-hist.active { border-left-color: #E50914; background: rgba(229, 9, 20, 0.09); }

/* ---------- Misc ---------- */
hr, [data-testid="stDivider"] hr { border-color: #330A0A !important; }
a, a:visited { color: #FF6B6B; }
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: #150505; }
::-webkit-scrollbar-thumb { background: #7F0000; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #E50914; }
[data-testid="stAlert"] { border-radius: 10px; border-left-width: 3px; }
</style>
"""


def inject() -> None:
    """Apply the theme. Call once, right after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="yt-hero"><h1>{title}</h1><p>{subtitle}</p>'
        f'<div class="rule"></div></div>',
        unsafe_allow_html=True,
    )
