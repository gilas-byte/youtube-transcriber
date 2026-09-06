"""Small custom widgets Streamlit does not ship with."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

_COPY_HTML = """
<style>
  html, body { margin: 0; padding: 0; background: transparent; }
  button {
      width: 100%;
      padding: 0.58rem 1.1rem;
      font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 0.95rem;
      font-weight: 650;
      letter-spacing: 0.015em;
      color: #FFFFFF;
      background: linear-gradient(135deg, #B00020 0%, #E50914 100%);
      border: 1px solid #FF1E1E;
      border-radius: 10px;
      cursor: pointer;
      transition: transform 0.12s ease, box-shadow 0.2s ease, filter 0.2s ease;
  }
  button:hover {
      filter: brightness(1.12);
      box-shadow: 0 0 22px rgba(229, 9, 20, 0.45);
      transform: translateY(-1px);
      border-color: #FF6B6B;
  }
  button:active { transform: translateY(0); }
  button.done { background: linear-gradient(135deg, #0F7A3D, #16A34A); border-color: #22C55E; }
  button.fail { background: #3A0A0A; border-color: #7F0000; color: #FFB3B3; }
</style>

<button id="yt-copy">__LABEL__</button>

<script>
  const TEXT = __PAYLOAD__;
  const BTN = document.getElementById("yt-copy");
  const LABEL = BTN.innerHTML;

  function flash(cls, label) {
      BTN.classList.add(cls);
      BTN.innerHTML = label;
      setTimeout(function () {
          BTN.classList.remove(cls);
          BTN.innerHTML = LABEL;
      }, 2000);
  }

  // Fallback for iframes where the async Clipboard API is blocked.
  function legacyCopy() {
      const area = document.createElement("textarea");
      area.value = TEXT;
      area.style.position = "fixed";
      area.style.top = "-1000px";
      area.setAttribute("readonly", "");
      document.body.appendChild(area);
      area.select();
      area.setSelectionRange(0, area.value.length);
      let ok = false;
      try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
      document.body.removeChild(area);
      return ok;
  }

  BTN.addEventListener("click", async function () {
      try {
          if (navigator.clipboard && window.isSecureContext) {
              await navigator.clipboard.writeText(TEXT);
              flash("done", "\\u2713 Copied!");
              return;
          }
          throw new Error("clipboard api unavailable");
      } catch (err) {
          const ok = legacyCopy();
          flash(ok ? "done" : "fail", ok ? "\\u2713 Copied!" : "\\u2717 Press Ctrl+C");
      }
  });
</script>
"""


def copy_button(text: str, label: str = "📋 Copy Text", height: int = 54) -> None:
    """A button that puts `text` on the user's clipboard, with a legacy fallback."""
    html = _COPY_HTML.replace("__PAYLOAD__", json.dumps(text)).replace("__LABEL__", label)
    components.html(html, height=height)


def chips(*items: tuple[str, bool]) -> str:
    """Build the chip row markup. Each item is (label, is_highlighted)."""
    parts = [
        f'<span class="yt-chip{"" if strong else " muted"}">{label}</span>'
        for label, strong in items
        if label
    ]
    return f'<div class="yt-chips">{"".join(parts)}</div>'
