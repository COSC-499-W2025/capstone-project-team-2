"""Resume & Portfolio page workflows for Streamlit.

This module contains both public and private interactions:
- Public mode: read-only loading + preview + download
- Private mode: full create/load/delete/edit workflows

Implementation approach:
- Reuse helpers from `streamlit_helpers.py` for API interactions and repeated
  editor UI components.
- Keep mode switching and top-level orchestration here.
"""

import streamlit as st
import requests
import time
import sys
from pathlib import Path


# Allow this page module to import shared frontend helpers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.web.mode import render_page_header
from src.web.streamlit_helpers import (
    API_BASE, THEMES, api_error, list_docs, fetch_doc,
    edit_contact_section, edit_summary_section, edit_theme_section,
    add_project_section, modify_entries_section, download_section,
    delete_doc_section, edit_connections_section,
    add_education_section, remove_education_section,
    add_experience_section, remove_experience_section,
)


def _mode_toggle_buttons(options: list[str], *, state_key: str) -> str:
    """Render a mode toggle row that mirrors sidebar button behavior.

    This helper avoids Streamlit segmented-control theme inconsistencies by
    rendering explicit buttons and applying key-scoped CSS per option.

    Args:
        options: Ordered option labels to render as toggle buttons.
        state_key: Session-state key used to persist the current selection.

    Returns:
        The currently selected option label.
    """
    if state_key not in st.session_state or st.session_state[state_key] not in options:
        st.session_state[state_key] = options[0]
    current = st.session_state[state_key]

    cols = st.columns([1] * len(options) + [max(2, len(options))], gap="small")
    for idx, option in enumerate(options):
        btn_key = f"{state_key}_{idx}"
        with cols[idx]:
            if st.button(
                option,
                key=btn_key,
                type="primary" if option == current else "secondary",
                use_container_width=True,
            ):
                st.session_state[state_key] = option
                st.rerun()

    return st.session_state[state_key]


def _render_readonly_doc_view(doc_id: str, doc: dict, endpoint_prefix: str, dl_key: str) -> None:
    """Render a read-only document preview with optional download.

    This is used in Public mode so users can inspect generated artifacts without
    exposing any edit/create/delete controls.

    Args:
        doc_id: Identifier of the selected document.
        doc: Parsed document payload from API.
        endpoint_prefix: API namespace (e.g., ``resume`` or ``portfolio``).
        dl_key: Session-state key prefix for download widget state.

    Returns:
        None. Renders read-only preview components directly.
    """
    st.info(f"Viewing {endpoint_prefix}: `{doc_id}`")
    st.caption(f"Theme: {doc.get('theme', 'unknown')}")

    contact = doc.get("contact") or {}
    with st.expander("Contact", expanded=True):
        st.write(
            {
                "name": contact.get("name", ""),
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "location": contact.get("location", ""),
                "website": contact.get("website", ""),
            }
        )

    with st.expander("Summary", expanded=True):
        st.write(doc.get("summary") or "No summary available.")

    connections = doc.get("connections") or []
    if connections:
        with st.expander("Connections", expanded=False):
            for c in connections:
                network = c.get("network", "")
                username = c.get("username", "")
                st.write(f"- {network}: {username}")

    for section_name in ("education", "experience", "projects", "skills"):
        section_data = doc.get(section_name) or []
        if not section_data:
            continue
        with st.expander(section_name.capitalize(), expanded=False):
            st.write(section_data)

    st.subheader("Download")
    download_section(doc_id, endpoint_prefix, dl_key)


def _public_document_tab(*, suffix: str, endpoint_prefix: str, id_key: str, data_key: str, dl_key: str) -> None:
    """Render read-only selector/view for public mode.

    State keys are passed in so resume and portfolio tabs can reuse this
    implementation without clobbering each other's session state.

    Args:
        suffix: File suffix used by the saved-document listing helper.
        endpoint_prefix: API namespace (e.g., ``resume`` or ``portfolio``).
        id_key: Session-state key storing active document ID.
        data_key: Session-state key storing fetched document data.
        dl_key: Session-state key prefix for download widget state.

    Returns:
        None. Renders public-mode controls and document preview.
    """
    st.session_state.setdefault(id_key, "")
    st.session_state.setdefault(data_key, None)
    existing = list_docs(suffix)

    if not existing:
        st.warning(f"No saved {endpoint_prefix}s found.")
        return

    with st.container(border=True):
        st.subheader(f"{endpoint_prefix.title()} Viewer")
        selected = st.selectbox(
            f"Select {endpoint_prefix}",
            existing,
            format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "),
            key=f"public_{endpoint_prefix}_select",
        )
        col1, col2, _ = st.columns([1, 1, 3], gap="small")
        with col1:
            if st.button(f"Load {endpoint_prefix.title()}", type="primary", key=f"public_{endpoint_prefix}_load"):
                st.session_state[id_key] = selected
                st.session_state[data_key] = None
                st.rerun()
        with col2:
            if st.session_state.get(id_key) and st.button("Close", key=f"public_{endpoint_prefix}_close"):
                st.session_state[id_key] = ""
                st.session_state[data_key] = None
                st.rerun()

    active_id = st.session_state.get(id_key)
    if not active_id:
        return

    doc = fetch_doc(data_key, active_id, endpoint_prefix)
    if doc is None:
        return
    _render_readonly_doc_view(active_id, doc, endpoint_prefix, dl_key)


def resume_tab() -> None:
    """Render the Resume tab with create, load, delete, edit, projects, and download workflows.

    Manages session state for the active resume ID and data. When no resume is active,
    shows options to create, load, or delete. When a resume is active, shows section
    editors for contact, summary, theme, education, experience, projects, and download.

    Returns:
        None: Renders Streamlit UI components directly
    """
    st.session_state.setdefault("resume_id", "")
    st.session_state.setdefault("resume_data", None)

    if not st.session_state.resume_id:
        existing = list_docs("Resume_CV")
        with st.container(border=True):
            st.subheader("Resume Workspace")
            with st.expander(f"{len(existing)} resume(s) found", expanded=False):
                for i, name in enumerate(existing, start=1):
                    st.caption(f"{i}. {name.rsplit('_', 1)[0].replace('_', ' ')}")
            mode = _mode_toggle_buttons(
                ["Create Resume", "Load Resume", "Delete Resume"],
                state_key="resume_mode_choice",
            )

        if mode == "Create Resume":
            with st.container(border=True):
                st.markdown("<p class='section-title'>Create Resume</p>", unsafe_allow_html=True)
                st.caption("Enter identity + theme, then generate a new resume artifact.")
                with st.form("resume_create_form"):
                    input_col, _ = st.columns([2.2, 2.8], gap="large")
                    with input_col:
                        name  = st.text_input("Full name", placeholder="e.g., Jane Doe")
                        theme = st.selectbox("Theme", THEMES)
                    action_col, _ = st.columns([1.15, 3.85], gap="small")
                    with action_col:
                        submit_resume = st.form_submit_button(
                            "Generate Resume",
                            type="primary",
                            icon=":material/add:",
                            use_container_width=True,
                        )
                    if submit_resume:
                        if not name.strip():
                            st.warning("Please enter a name.", icon=":material/warning:")
                        else:
                            resp = requests.post(f"{API_BASE}/resume/generate", json={"name": name.strip(), "theme": theme})
                            if resp.ok:
                                st.session_state.resume_id = resp.json()["resume_id"]
                                st.rerun()
                            else:
                                st.error(api_error(resp))
        elif mode == "Load Resume":
            with st.container(border=True):
                st.subheader("Load Resume")
                if not existing:
                    st.warning("No saved resumes were found. Please create one first.")
                else:
                    selected = st.selectbox(
                        "Select resume",
                        existing,
                        format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "),
                    )
                    if st.button("Load Resume", type="primary", icon=":material/drive_folder_upload:"):
                        st.session_state.resume_id = selected
                        st.session_state.resume_data = None
                        st.rerun()
        elif mode == "Delete Resume":
            with st.container(border=True):
                st.subheader("Delete Resume")
                delete_doc_section(existing, "resume", "resume_del")

    else:
        resume_id = st.session_state.resume_id
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.subheader("Active Resume")
                st.caption(f"`{resume_id}`")
            with col2:
                if st.button("Close", icon=":material/close:", key="resume_close"):
                    st.session_state.resume_id = ""
                    st.session_state.resume_data = None
                    st.session_state.pop("resume_dl_bytes", None)
                    st.session_state.pop("resume_dl_rendered", None)
                    st.rerun()

        rd = fetch_doc("resume_data", resume_id, "resume")
        if rd is None:
            return

        if msg := st.session_state.pop("_flash_success", None):
            flash = st.empty()
            flash.success(msg)
            time.sleep(2)
            flash.empty()

        section = _mode_toggle_buttons(
            ["Edit", "Projects", "Download"],
            state_key="resume_section_choice",
        )
        invalidate = lambda: st.session_state.update({"resume_data": None})

        if section == "Edit":
            with st.container(border=True):
                category = st.selectbox(
                    "Select category",
                    ["Contact Info", "Summary", "Theme", "Education", "Experience", "Connections"],
                    key="resume_edit_cat",
                )
                if category == "Contact Info":
                    edit_contact_section(resume_id, rd, "resume", invalidate)
                elif category == "Summary":
                    edit_summary_section(resume_id, rd, "resume", invalidate)
                elif category == "Theme":
                    edit_theme_section(resume_id, rd, "resume", invalidate)
                elif category == "Education":
                    edu_action = _mode_toggle_buttons(
                        ["Add Education", "Modify Education", "Remove Education"],
                        state_key="resume_edu_action_choice",
                    )
                    if edu_action == "Add Education":
                        add_education_section(resume_id, invalidate)
                    elif edu_action == "Modify Education":
                        modify_entries_section(
                            resume_id,
                            rd,
                            "education",
                            "institution",
                            ["institution", "area", "degree", "start_date", "end_date", "location", "gpa", "highlights"],
                            "resume",
                            invalidate,
                        )
                    elif edu_action == "Remove Education":
                        remove_education_section(resume_id, rd, invalidate)
                elif category == "Experience":
                    exp_action = _mode_toggle_buttons(
                        ["Add Experience", "Modify Experience", "Remove Experience"],
                        state_key="resume_exp_action_choice",
                    )
                    if exp_action == "Add Experience":
                        add_experience_section(resume_id, invalidate)
                    elif exp_action == "Modify Experience":
                        modify_entries_section(
                            resume_id,
                            rd,
                            "experience",
                            "company",
                            ["company", "position", "start_date", "end_date", "location", "summary", "highlights"],
                            "resume",
                            invalidate,
                        )
                    elif exp_action == "Remove Experience":
                        remove_experience_section(resume_id, rd, invalidate)
                elif category == "Connections":
                    edit_connections_section(resume_id, rd, "resume", invalidate)
        elif section == "Projects":
            with st.container(border=True):
                action = _mode_toggle_buttons(
                    ["Add Project", "Modify Project"],
                    state_key="resume_proj_action_choice",
                )
                if action == "Add Project":
                    add_project_section(resume_id, "resume", invalidate)
                elif action == "Modify Project":
                    modify_entries_section(
                        resume_id,
                        rd,
                        "projects",
                        "name",
                        ["summary", "highlights", "start_date", "end_date", "location", "name"],
                        "resume",
                        invalidate,
                    )
        elif section == "Download":
            with st.container(border=True):
                st.subheader("Download Resume")
                download_section(resume_id, "resume", "resume_dl")


def portfolio_tab() -> None:
    """Render the Portfolio tab with create, load, delete, edit, projects, and download workflows.

    Manages session state for the active portfolio ID and data. When no portfolio is active,
    shows options to create, load, or delete. When a portfolio is active, shows section
    editors for contact, summary, theme, connections, projects, and download.

    Returns:
        None: Renders Streamlit UI components directly
    """
    st.session_state.setdefault("portfolio_id", "")
    st.session_state.setdefault("portfolio_data", None)

    if not st.session_state.portfolio_id:
        existing = list_docs("Portfolio_CV")
        with st.container(border=True):
            st.subheader("Portfolio Workspace")
            with st.expander(f"{len(existing)} portfolio(s) found", expanded=False):
                for i, name in enumerate(existing, start=1):
                    st.caption(f"{i}. {name.rsplit('_', 1)[0].replace('_', ' ')}")
            mode = _mode_toggle_buttons(
                ["Create Portfolio", "Load Portfolio", "Delete Portfolio"],
                state_key="portfolio_mode_choice",
            )

        if mode == "Create Portfolio":
            with st.container(border=True):
                st.markdown("<p class='section-title'>Create Portfolio</p>", unsafe_allow_html=True)
                st.caption("Enter identity + theme, then generate a new portfolio artifact.")
                with st.form("portfolio_create_form"):
                    input_col, _ = st.columns([2.2, 2.8], gap="large")
                    with input_col:
                        name  = st.text_input("Full name", placeholder="e.g., Jane Doe")
                        theme = st.selectbox("Theme", THEMES, key="portfolio_gen_theme")
                    action_col, _ = st.columns([1.2, 3.8], gap="small")
                    with action_col:
                        submit_portfolio = st.form_submit_button(
                            "Generate Portfolio",
                            type="primary",
                            icon=":material/add:",
                            use_container_width=True,
                        )
                    if submit_portfolio:
                        if not name.strip():
                            st.warning("Please enter a name.", icon=":material/warning:")
                        else:
                            resp = requests.post(f"{API_BASE}/portfolio/generate", json={"name": name.strip(), "theme": theme})
                            if resp.ok:
                                st.session_state.portfolio_id = resp.json()["portfolio_id"]
                                st.rerun()
                            else:
                                st.error(api_error(resp))
        elif mode == "Load Portfolio":
            with st.container(border=True):
                st.subheader("Load Portfolio")
                if not existing:
                    st.warning("No saved portfolios found. Please create one first.")
                else:
                    selected = st.selectbox(
                        "Select portfolio",
                        existing,
                        key="portfolio_load_select",
                        format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "),
                    )
                    if st.button("Load Portfolio", type="primary", icon=":material/drive_folder_upload:", key="portfolio_load_btn"):
                        st.session_state.portfolio_id = selected
                        st.session_state.portfolio_data = None
                        st.rerun()
        elif mode == "Delete Portfolio":
            with st.container(border=True):
                st.subheader("Delete Portfolio")
                delete_doc_section(existing, "portfolio", "portfolio_del")
    else:
        portfolio_id = st.session_state.portfolio_id
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.subheader("Active Portfolio")
                st.caption(f"`{portfolio_id}`")
            with col2:
                if st.button("Close", icon=":material/close:", key="portfolio_close"):
                    st.session_state.portfolio_id = ""
                    st.session_state.portfolio_data = None
                    st.session_state.pop("portfolio_dl_bytes", None)
                    st.session_state.pop("portfolio_dl_rendered", None)
                    st.rerun()

        pd_ = fetch_doc("portfolio_data", portfolio_id, "portfolio")
        if pd_ is None:
            return

        if msg := st.session_state.pop("_flash_success", None):
            flash = st.empty()
            flash.success(msg)
            time.sleep(2)
            flash.empty()

        section = _mode_toggle_buttons(
            ["Edit", "Projects", "Download"],
            state_key="portfolio_section_choice",
        )
        invalidate = lambda: st.session_state.update({"portfolio_data": None})

        if section == "Edit":
            with st.container(border=True):
                category = st.selectbox(
                    "Select category",
                    ["Contact Info", "Summary", "Theme", "Connections"],
                    key="portfolio_edit_cat",
                )
                if category == "Contact Info":
                    edit_contact_section(portfolio_id, pd_, "portfolio", invalidate)
                elif category == "Summary":
                    edit_summary_section(portfolio_id, pd_, "portfolio", invalidate)
                elif category == "Theme":
                    edit_theme_section(portfolio_id, pd_, "portfolio", invalidate)
                elif category == "Connections":
                    edit_connections_section(portfolio_id, pd_, "portfolio", invalidate)
        elif section == "Projects":
            with st.container(border=True):
                action = _mode_toggle_buttons(
                    ["Add Project", "Modify Project"],
                    state_key="portfolio_proj_action_choice",
                )
                if action == "Add Project":
                    add_project_section(portfolio_id, "portfolio", invalidate)
                elif action == "Modify Project":
                    modify_entries_section(
                        portfolio_id,
                        pd_,
                        "projects",
                        "name",
                        ["summary", "highlights", "start_date", "end_date", "location", "name"],
                        "portfolio",
                        invalidate,
                    )
        elif section == "Download":
            with st.container(border=True):
                st.subheader("Download Portfolio")
                download_section(portfolio_id, "portfolio", "portfolio_dl")


def render_page() -> None:
    """Render the resume and portfolio workspace page.

    Returns:
        None. Renders tabs and mode-gated workflows directly.
    """
    mode = render_page_header(
        "Resume & Portfolio",
        "Create, edit, and export resume and portfolio documents.",
    )
    st.markdown(
        """
        <div class="page-hero">
            <h3>Document Workspace</h3>
            <p>Build and refine resume + portfolio artifacts with mode-aware editing and download flows.</p>
            <div class="page-chip-row">
                <span class="page-chip">Create / Load</span>
                <span class="page-chip">Edit Sections</span>
                <span class="page-chip">Download Output</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("doc_workspace_mode", "resume")
    current_doc_mode = st.session_state["doc_workspace_mode"]
    active_doc_label = "Resume" if current_doc_mode == "resume" else "Portfolio"

    with st.container(border=True):
        title_col, chip_col = st.columns([5, 2], gap="small")
        with title_col:
            st.markdown("<p class='section-title'>Document Type</p>", unsafe_allow_html=True)
        with chip_col:
            st.markdown(
                f"<div class='chip-align-right'><span class='page-chip'>Active: {active_doc_label}</span></div>",
                unsafe_allow_html=True,
            )
        st.caption("Choose which document workspace to open.")

        doc_col1, doc_col2, _ = st.columns([1.1, 1.2, 3.7], gap="small")
        with doc_col1:
            if st.button(
                "Resume",
                key="doc_seg_resume",
                type="primary" if current_doc_mode == "resume" else "secondary",
                icon=":material/description:",
                use_container_width=True,
            ):
                st.session_state["doc_workspace_mode"] = "resume"
                st.rerun()
        with doc_col2:
            if st.button(
                "Portfolio",
                key="doc_seg_portfolio",
                type="primary" if current_doc_mode == "portfolio" else "secondary",
                icon=":material/workspace_premium:",
                use_container_width=True,
            ):
                st.session_state["doc_workspace_mode"] = "portfolio"
                st.rerun()

    if mode == "Public":
        st.info("Public mode: read-only preview and download only.")
        if st.session_state["doc_workspace_mode"] == "resume":
            _public_document_tab(
                suffix="Resume_CV",
                endpoint_prefix="resume",
                id_key="public_resume_id",
                data_key="public_resume_data",
                dl_key="public_resume_dl",
            )
        else:
            _public_document_tab(
                suffix="Portfolio_CV",
                endpoint_prefix="portfolio",
                id_key="public_portfolio_id",
                data_key="public_portfolio_data",
                dl_key="public_portfolio_dl",
            )
        return

    if st.session_state["doc_workspace_mode"] == "resume":
        resume_tab()
    else:
        portfolio_tab()


if __name__ == "__main__":
    render_page()
