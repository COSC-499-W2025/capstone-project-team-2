"""Main Streamlit shell for Milestone 3 workflows."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.web.mode import render_mode_sidebar


def main() -> None:
    """Render the Streamlit home page.

    Navigation is intentionally handled by Streamlit's built-in multipage sidebar.
    """
    st.set_page_config(page_title="Mining Digital Work Artifacts", layout="wide")
    render_mode_sidebar()
    st.title("Mining Digital Work Artifacts")
    st.caption("Use the left sidebar to open Dashboard or Resume & Portfolio pages.")
    st.divider()

    st.subheader("Home")
    st.caption(f"Current mode: **{st.session_state.view_mode}**")
    st.caption("API base URL is configured in `src/web/streamlit_helpers.py`.")


if __name__ == "__main__":
    main()
