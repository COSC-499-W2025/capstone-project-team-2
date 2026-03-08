"""Shared view mode helpers for Streamlit pages."""

from __future__ import annotations

import streamlit as st


def render_mode_sidebar() -> str:
    """Render the global mode toggle in the sidebar and return the selected mode.

    This centralizes mode handling so every page can apply the same Public/Private
    semantics without duplicating sidebar widgets or state key conventions.
    """
    options = ["Private", "Public"]
    st.session_state.setdefault("view_mode", "Private")
    if st.session_state.view_mode not in options:
        st.session_state.view_mode = "Private"

    with st.sidebar:
        st.markdown("### View Mode")
        selected_mode = st.radio(
            "Mode",
            options=options,
            index=options.index(st.session_state.view_mode),
            label_visibility="collapsed",
            help="Private mode allows customization. Public mode is read-only.",
        )

    # Single source of truth used by every page.
    st.session_state.view_mode = selected_mode
    return st.session_state.view_mode