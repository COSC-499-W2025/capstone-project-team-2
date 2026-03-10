"""Main Streamlit shell for Milestone 3 workflows.

Responsibilities:
- bootstraps page config
- renders the global sidebar mode controls
- builds mode-aware navigation
- delegates actual page content to page modules

Why this file is intentionally thin:
- keeps app entry-point predictable
- avoids duplicating UI logic that already exists in shared helpers
"""

import sys
from pathlib import Path

import streamlit as st


# Allow running this module directly from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.web.mode import render_mode_sidebar, render_page_header


def _render_home_page() -> None:
    """Render the home page content.

    Returns:
        None. Renders Streamlit components directly.
    """
    render_page_header(
        "Mining Digital Work Artifacts",
        "Use the left sidebar to open available pages.",
    )
    st.markdown(
        """
        <div class="page-hero">
            <h3>Home Workspace</h3>
            <p>Use the left navigation to move between analytics, document builders, and private tools.</p>
            <div class="page-chip-row">
                <span class="page-chip">Dashboard Insights</span>
                <span class="page-chip">Resume & Portfolio</span>
                <span class="page-chip">Config + Upload Tools</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown("<p class='section-title'>Environment</p>", unsafe_allow_html=True)
        st.caption("API base URL is configured in `src/web/streamlit_helpers.py`.")


def _navigation_for_mode(mode: str) -> dict[str, list[st.Page]]:
    """Build navigation groups based on current view mode.

    Args:
        mode: Current global mode (`Private` or `Public`).

    Returns:
        A mapping of sidebar section labels to Streamlit pages.
    """
    # Workspace pages are always available in both modes because they are
    # safe to browse in read-only public contexts.
    pages: dict[str, list[st.Page]] = {
        "Workspace": [
            st.Page(_render_home_page, title="Home", icon=":material/home:", default=True),
            st.Page("pages/Dashboard.py", title="Dashboard", icon=":material/insights:"),
            st.Page("pages/ResumeAndPortfoiloMaker.py", title="Resume & Portfolio", icon=":material/description:"),
        ]
    }

    if mode == "Private":
        pages["Private Tools"] = [
            st.Page("pages/project_upload_page.py", title="Project Upload", icon=":material/upload_file:"),
            st.Page("pages/UserConfiguration.py", title="User Configuration", icon=":material/settings:"),
        ]
    return pages


def main() -> None:
    """Run the Streamlit app shell.

    Returns:
        None. Configures Streamlit, renders navigation, and executes active page.
    """
    st.set_page_config(
        page_title="Mining Digital Work Artifacts",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    mode = render_mode_sidebar()
    nav = st.navigation(_navigation_for_mode(mode))
    nav.run()


if __name__ == "__main__":
    main()
