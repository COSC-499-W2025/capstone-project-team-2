import streamlit as st
import requests
import time
import sys
from pathlib import Path

# Add project root to path so we can import src.web.streamlit_helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.web.mode import render_mode_sidebar
from src.web.streamlit_helpers import (
    API_BASE, THEMES, api_error, list_docs, fetch_doc,
    edit_contact_section, edit_summary_section, edit_theme_section,
    add_project_section, modify_entries_section, download_section,
    delete_doc_section, edit_connections_section,
    add_education_section, remove_education_section,
    add_experience_section, remove_experience_section,
)


def _render_readonly_doc_view(doc_id: str, doc: dict, endpoint_prefix: str, dl_key: str) -> None:
    """Render a read-only document preview with optional download.

    This is used in Public mode so users can inspect generated artifacts without
    exposing any edit/create/delete controls.
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

    st.markdown("### Download")
    download_section(doc_id, endpoint_prefix, dl_key)


def _public_document_tab(*, suffix: str, endpoint_prefix: str, id_key: str, data_key: str, dl_key: str) -> None:
    """Render read-only selector/view for public mode.

    State keys are passed in so resume and portfolio tabs can reuse this
    implementation without clobbering each other's session state.
    """
    st.session_state.setdefault(id_key, "")
    st.session_state.setdefault(data_key, None)
    existing = list_docs(suffix)

    if not existing:
        st.warning(f"No saved {endpoint_prefix}s found.")
        return

    # Public mode supports selection + viewing only.
    selected = st.selectbox(
        f"Select {endpoint_prefix}",
        existing,
        format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "),
        key=f"public_{endpoint_prefix}_select",
    )
    col1, col2 = st.columns([1, 1])
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

    # Pull fresh data on-demand for the selected document.
    doc = fetch_doc(data_key, active_id, endpoint_prefix)
    if doc is None:
        return
    _render_readonly_doc_view(active_id, doc, endpoint_prefix, dl_key)


def resume_tab():
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
        with st.expander(f"📄 {len(existing)} resume(s) found", expanded=False):
            for i, name in enumerate(existing, start=1):
                st.caption(f"{i}. {name.rsplit('_', 1)[0].replace('_', ' ')}")
        mode = st.segmented_control("Mode", ["➕ Create Resume", "📂 Load Resume", "🗑️ Delete Resume"],
                                    label_visibility="hidden", default="➕ Create Resume")
        if mode == "➕ Create Resume":
            with st.form("resume_create_form"):
                name  = st.text_input("Full name", placeholder="e.g., Jane Doe")
                theme = st.selectbox("Theme", THEMES)
                if st.form_submit_button("Generate Resume", type="primary", icon=":material/add:"):
                    if not name.strip():
                        st.warning("Please enter a name.", icon=":material/warning:")
                    else:
                        resp = requests.post(f"{API_BASE}/resume/generate", json={"name": name.strip(), "theme": theme})
                        if resp.ok:
                            st.session_state.resume_id = resp.json()["resume_id"]
                            st.rerun()
                        else:
                            st.error(api_error(resp))
        elif mode == "📂 Load Resume":
            if not existing:
                st.warning("No saved resumes were found. Please create one first.")
            else:
                selected = st.selectbox("Select resume", existing,
                                        format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "))
                if st.button("Load Resume", type="primary", icon=":material/drive_folder_upload:"):
                    st.session_state.resume_id = selected
                    st.session_state.resume_data = None
                    st.rerun()
        elif mode == "🗑️ Delete Resume":
            delete_doc_section(existing, "resume", "resume_del")

    else:
        resume_id = st.session_state.resume_id
        col1, col2 = st.columns([5, 1])
        with col1:
            st.info(f"Active resume: `{resume_id}`")
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
        section = st.segmented_control("Section", ["✏️ Edit", "📊 Projects", "⬇️ Download"],
                                       label_visibility="hidden", key="resume_section")
        invalidate = lambda: st.session_state.update({"resume_data": None})

        if section == "✏️ Edit":
            category = st.selectbox("Select category",
                                    ["Contact Info", "Summary", "Theme", "Education", "Experience", "Connections"],
                                    key="resume_edit_cat")
            if category == "Contact Info":
                edit_contact_section(resume_id, rd, "resume", invalidate)
            elif category == "Summary":
                edit_summary_section(resume_id, rd, "resume", invalidate)
            elif category == "Theme":
                edit_theme_section(resume_id, rd, "resume", invalidate)
            elif category == "Education":
                edu_action = st.segmented_control("Action", ["➕ Add Education", "✏️ Modify Education", "🗑️ Remove Education"],
                                                  label_visibility="hidden", key="resume_edu_action")
                if edu_action == "➕ Add Education":
                    add_education_section(resume_id, invalidate)
                elif edu_action == "✏️ Modify Education":
                    modify_entries_section(resume_id, rd, "education", "institution",
                                          ["institution", "area", "degree", "start_date", "end_date", "location", "gpa", "highlights"],
                                          "resume", invalidate)
                elif edu_action == "🗑️ Remove Education":
                    remove_education_section(resume_id, rd, invalidate)
            elif category == "Experience":
                exp_action = st.segmented_control("Action", ["➕ Add Experience", "✏️ Modify Experience", "🗑️ Remove Experience"],
                                                  label_visibility="hidden", key="resume_exp_action")
                if exp_action == "➕ Add Experience":
                    add_experience_section(resume_id, invalidate)
                elif exp_action == "✏️ Modify Experience":
                    modify_entries_section(resume_id, rd, "experience", "company",
                                          ["company", "position", "start_date", "end_date", "location", "summary", "highlights"],
                                          "resume", invalidate)
                elif exp_action == "🗑️ Remove Experience":
                    remove_experience_section(resume_id, rd, invalidate)
            elif category == "Connections":
                edit_connections_section(resume_id, rd, "resume", invalidate)
        elif section == "📊 Projects":
            action = st.segmented_control("Action", ["➕ Add Project", "✏️ Modify Project"],
                                          label_visibility="hidden", key="resume_proj_action")
            if action == "➕ Add Project":
                add_project_section(resume_id, "resume", invalidate)
            elif action == "✏️ Modify Project":
                modify_entries_section(resume_id, rd, "projects", "name",
                                      ["summary", "highlights", "start_date", "end_date", "location", "name"],
                                      "resume", invalidate)
        elif section == "⬇️ Download":
            download_section(resume_id, "resume", "resume_dl")


def portfolio_tab():
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
        with st.expander(f"📄 {len(existing)} portfolio(s) found", expanded=False):
            for i, name in enumerate(existing, start=1):
                st.caption(f"{i}. {name.rsplit('_', 1)[0].replace('_', ' ')}")
        mode = st.segmented_control("Mode", ["➕ Create Portfolio", "📂 Load Portfolio", "🗑️ Delete Portfolio"],
                                    label_visibility="hidden", default="➕ Create Portfolio", key="portfolio_mode")
        if mode == "➕ Create Portfolio":
            with st.form("portfolio_create_form"):
                name  = st.text_input("Full name", placeholder="e.g., Jane Doe")
                theme = st.selectbox("Theme", THEMES, key="portfolio_gen_theme")
                if st.form_submit_button("Generate Portfolio", type="primary", icon=":material/add:"):
                    if not name.strip():
                        st.warning("Please enter a name.", icon=":material/warning:")
                    else:
                        resp = requests.post(f"{API_BASE}/portfolio/generate", json={"name": name.strip(), "theme": theme})
                        if resp.ok:
                            st.session_state.portfolio_id = resp.json()["portfolio_id"]
                            st.rerun()
                        else:
                            st.error(api_error(resp))
        elif mode == "📂 Load Portfolio":
            if not existing:
                st.warning("No saved portfolios found. Please create one first.")
            else:
                selected = st.selectbox("Select portfolio", existing, key="portfolio_load_select",
                                        format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "))
                if st.button("Load Portfolio", type="primary", icon=":material/drive_folder_upload:", key="portfolio_load_btn"):
                    st.session_state.portfolio_id = selected
                    st.session_state.portfolio_data = None
                    st.rerun()
        elif mode == "🗑️ Delete Portfolio":
            delete_doc_section(existing, "portfolio", "portfolio_del")
    else:
        portfolio_id = st.session_state.portfolio_id
        col1, col2 = st.columns([5, 1])
        with col1:
            st.info(f"Active portfolio: `{portfolio_id}`")
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
        section = st.segmented_control("Section", ["✏️ Edit", "📊 Projects", "⬇️ Download"],
                                       label_visibility="hidden", key="portfolio_section")
        invalidate = lambda: st.session_state.update({"portfolio_data": None})

        if section == "✏️ Edit":
            category = st.selectbox("Select category", ["Contact Info", "Summary", "Theme", "Connections"], key="portfolio_edit_cat")
            if category == "Contact Info":
                edit_contact_section(portfolio_id, pd_, "portfolio", invalidate)
            elif category == "Summary":
                edit_summary_section(portfolio_id, pd_, "portfolio", invalidate)
            elif category == "Theme":
                edit_theme_section(portfolio_id, pd_, "portfolio", invalidate)
            elif category == "Connections":
                edit_connections_section(portfolio_id, pd_, "portfolio", invalidate)
        elif section == "📊 Projects":
            action = st.segmented_control("Action", ["➕ Add Project", "✏️ Modify Project"],
                                          label_visibility="hidden", key="portfolio_proj_action")
            if action == "➕ Add Project":
                add_project_section(portfolio_id, "portfolio", invalidate)
            elif action == "✏️ Modify Project":
                modify_entries_section(portfolio_id, pd_, "projects", "name",
                                      ["summary", "highlights", "start_date", "end_date", "location", "name"],
                                      "portfolio", invalidate)
        elif section == "⬇️ Download":
            download_section(portfolio_id, "portfolio", "portfolio_dl")


def render_page():
    """Render the resume and portfolio workspace page."""
    mode = render_mode_sidebar()
    st.title("📄 Resume & Portfolio Maker")
    if mode == "Public":
        # Public = read-only previews + export/download only.
        st.info("Public mode: read-only preview and download only.")
        tab_resume, tab_portfolio = st.tabs(["Resume", "Portfolio"])
        with tab_resume:
            _public_document_tab(
                suffix="Resume_CV",
                endpoint_prefix="resume",
                id_key="public_resume_id",
                data_key="public_resume_data",
                dl_key="public_resume_dl",
            )
        with tab_portfolio:
            _public_document_tab(
                suffix="Portfolio_CV",
                endpoint_prefix="portfolio",
                id_key="public_portfolio_id",
                data_key="public_portfolio_data",
                dl_key="public_portfolio_dl",
            )
        return
    # Private = full CRUD/editing workflows.
    tab_resume, tab_portfolio = st.tabs(["Resume", "Portfolio"])
    with tab_resume:
        resume_tab()
    with tab_portfolio:
        portfolio_tab()


if __name__ == "__main__":
    render_page()