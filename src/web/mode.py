"""Shared view mode helpers for Streamlit pages."""

from __future__ import annotations

import streamlit as st


def _sync_view_mode_from_widget() -> None:
    """Persist the sidebar selection into shared app session state."""
    st.session_state.view_mode = st.session_state._view_mode_widget


def render_mode_sidebar() -> str:
    """Render the global mode toggle in the sidebar and return the selected mode.

    This centralizes mode handling so every page can apply the same Public/Private
    semantics without duplicating sidebar widgets or state key conventions.
    """
    options = ["Private", "Public"]
    st.session_state.setdefault("view_mode", "Private")
    if st.session_state.view_mode not in options:
        st.session_state.view_mode = "Private"
    st.session_state["_view_mode_widget"] = st.session_state.view_mode

    with st.sidebar:
        st.markdown("### View Mode")
        st.radio(
            "Mode",
            options=options,
            key="_view_mode_widget",
            label_visibility="collapsed",
            help="Private mode allows customization. Public mode is read-only.",
            on_change=_sync_view_mode_from_widget,
        )

    return st.session_state.view_mode
