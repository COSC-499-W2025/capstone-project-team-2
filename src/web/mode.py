"""Shared view mode helpers for Streamlit pages.

This module is the UI consistency anchor for the Streamlit frontend:
- loads and injects global CSS
- controls app-wide Public/Private mode state
- renders the sidebar mode switcher
- exposes shared page-header rendering
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st

_STYLES_PATH = Path(__file__).resolve().parent / "styles" / "main.css"


@lru_cache(maxsize=1)
def _load_shared_css() -> str:
    """Read shared web CSS from disk once per process.

    Returns:
        The CSS text, or an empty string when unavailable.
    """
    try:
        return _STYLES_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def _inject_sidebar_styles() -> None:
    """Inject global frontend CSS into the current page.

    Returns:
        None. Writes a `<style>` block to the Streamlit page when CSS exists.
    """
    css = _load_shared_css()
    if not css:
        return
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


def _ensure_mode_state() -> None:
    """Initialize and sanitize shared view mode state.

    Returns:
        None. Ensures `st.session_state.view_mode` is always valid.
    """
    options = {"Private", "Public"}
    st.session_state.setdefault("view_mode", "Private")
    if st.session_state.view_mode not in options:
        st.session_state.view_mode = "Private"


def get_view_mode() -> str:
    """Return current view mode with safe default initialization.

    Returns:
        The current mode value (`Private` or `Public`).
    """
    _ensure_mode_state()
    return st.session_state.view_mode


def render_page_header(title: str, subtitle: str | None = None, *, show_mode: bool = True) -> str:
    """Render a consistent page header and return current mode.

    Args:
        title: Page title text.
        subtitle: Optional page subtitle/caption.
        show_mode: Whether to render the current mode caption.

    Returns:
        The current mode value after initialization.
    """
    _inject_sidebar_styles()
    mode = get_view_mode()
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    if show_mode:
        st.caption(f"Mode: **{mode}**")
    st.divider()
    return mode


def render_mode_sidebar() -> str:
    """Render sidebar mode controls and return the selected mode.

    This centralizes mode handling so every page can apply the same Public/Private
    semantics without duplicating sidebar widgets or state key conventions.

    Returns:
        The selected mode after rendering sidebar controls.
    """
    _ensure_mode_state()
    _inject_sidebar_styles()

    with st.sidebar:
        current = st.session_state.view_mode

        with st.container(border=True):
            st.markdown("<p class='mode-title'>Mode</p>", unsafe_allow_html=True)
            private_col, public_col = st.columns(2, gap="small")
            with private_col:
                if st.button(
                    "Private",
                    key="_mode_private_btn",
                    type="primary" if current == "Private" else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.view_mode = "Private"
                    st.rerun()
            with public_col:
                if st.button(
                    "Public",
                    key="_mode_public_btn",
                    type="primary" if current == "Public" else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.view_mode = "Public"
                    st.rerun()
            st.markdown(
                """
                <div class="mode-help">
                    <p><strong>Private:</strong> edit/customize.</p>
                    <p><strong>Public:</strong> read-only (search/filter).</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    return st.session_state.view_mode


def require_private_mode(page_name: str) -> str:
    """Block restricted pages when the app is in Public mode.

    Args:
        page_name: Human-readable page name for user-facing messages.

    Returns:
        The current mode value when access is allowed.
    """
    mode = get_view_mode()
    if mode == "Public":
        st.warning(f"`{page_name}` is available only in Private mode.")
        st.info("Switch the left panel mode to `Private (Edit)` to access this page.")
        st.stop()
    return mode
