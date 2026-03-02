"""
Shared helper functions for the Streamlit Resume & Portfolio UI.

Contains reusable components for API communication, document CRUD,
and section editors (contact, summary, theme, projects, entries,
connections, downloads).
"""
import re
import streamlit as st
import requests
import pendulum
from pathlib import Path

API_BASE = "http://localhost:8000"
CV_FILES_DIR = Path(__file__).resolve().parents[2] / "User_config_files" / "Generate_render_CV_files"
THEMES = ["sb2nov", "classic", "moderncv", "engineeringresumes"]
FORMATS = ["pdf", "html", "markdown"]
SOCIAL_NETWORKS = [
    "LinkedIn", "GitHub", "GitLab", "Bitbucket", "StackOverflow",
    "ResearchGate", "ORCID", "Google Scholar", "Instagram", "Twitter",
    "YouTube", "Medium",
]
MIME_TYPES = {"pdf": "application/pdf", "html": "text/html", "markdown": "text/markdown"}
FILE_EXTS = {"pdf": "pdf", "html": "html", "markdown": "md"}

_API_ID_RE = re.compile(r'_[0-9a-f]{8}$')


def list_docs(suffix: str) -> list:
    """Return names of API-generated documents (those with a UUID suffix)."""
    return sorted(
        stem for p in CV_FILES_DIR.glob(f"*_{suffix}.yaml")
        if _API_ID_RE.search(stem := p.name.removesuffix(f"_{suffix}.yaml"))
    )


def api_error(res) -> str:
    try:
        return res.json().get("detail", res.text)
    except Exception:
        return res.text


def fetch_doc(cache_key, doc_id, url_prefix):
    if st.session_state.get(cache_key) is None:
        try:
            resp = requests.get(f"{API_BASE}/{url_prefix}/{doc_id}", timeout=10)
            if not resp.ok:
                st.error(api_error(resp))
                return None
            st.session_state[cache_key] = resp.json()
        except requests.ConnectionError:
            st.error("Cannot reach API server.")
            return None
    return st.session_state[cache_key]


def fetch_projects():
    if st.session_state.get("projects_cache") is None:
        try:
            st.session_state.projects_cache = requests.get(f"{API_BASE}/projects/", timeout=10).json()
        except Exception:
            st.session_state.projects_cache = []
    return st.session_state.projects_cache


def fetch_project_info(project_name):
    cache = st.session_state.setdefault("project_info_cache", {})
    if project_name not in cache:
        try:
            resp = requests.get(f"{API_BASE}/projects/{project_name}", timeout=10)
            cache[project_name] = resp.json() if resp.ok else {}
        except Exception:
            cache[project_name] = {}
    return cache.get(project_name, {})


def post_edit(endpoint_prefix, doc_id, edits, invalidate_fn, success_msg):
    res = requests.post(f"{API_BASE}/{endpoint_prefix}/{doc_id}/edit", json={"edits": edits}, timeout=15)
    if res.ok:
        invalidate_fn()
        st.session_state["_flash_success"] = success_msg
        st.rerun()
    else:
        st.error(api_error(res))


def edit_contact_section(doc_id, rd, endpoint_prefix, invalidate_fn):
    contact = rd.get("contact") or {}
    with st.container(border=True):
        st.markdown("**Current contact info:**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption(f"Name: {contact.get('name', '—')}")
            st.caption(f"Email: {contact.get('email', '—')}")
        with c2:
            st.caption(f"Phone: {contact.get('phone', '—')}")
            st.caption(f"Location: {contact.get('location', '—')}")
        with c3:
            st.caption(f"Website: {contact.get('website', '—')}")
    with st.form(f"edit_contact_{endpoint_prefix}", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            r_name  = st.text_input("Name",     value=contact.get("name", ""))
            r_email = st.text_input("Email",    value=contact.get("email", ""))
        with c2:
            r_phone    = st.text_input("Phone",    value=contact.get("phone", ""))
            r_location = st.text_input("Location", value=contact.get("location", ""))
        with c3:
            r_website = st.text_input("Website", value=contact.get("website", ""))
        if st.form_submit_button("Save Contact", type="primary", icon=":material/save:"):
            edits = [
                {"section": "contact", "item_name": "", "field": f, "new_value": v}
                for f, v in {"name": r_name, "email": r_email, "phone": r_phone,
                             "location": r_location, "website": r_website}.items() if v
            ]
            post_edit(endpoint_prefix, doc_id, edits, invalidate_fn, "Contact info updated.")


def edit_summary_section(doc_id, rd, endpoint_prefix, invalidate_fn):
    current = rd.get("summary") or ""
    with st.container(border=True):
        st.markdown("**Current summary:**")
        st.text_area("cur_summary", value=current or "_(empty)_", disabled=True,
                     label_visibility="hidden", height=100, key=f"cur_summary_{endpoint_prefix}")
    with st.form(f"edit_summary_{endpoint_prefix}", clear_on_submit=False):
        new_summary = st.text_area("New summary", value=current, height=120)
        if st.form_submit_button("Update Summary", type="primary", icon=":material/sync:"):
            post_edit(endpoint_prefix, doc_id,
                      [{"section": "summary", "item_name": "", "field": "", "new_value": new_summary}],
                      invalidate_fn, "Summary updated.")


def edit_theme_section(doc_id, rd, endpoint_prefix, invalidate_fn):
    current_theme = rd.get("theme") or "sb2nov"
    with st.container(border=True):
        st.markdown(f"Current theme: **{current_theme}**")
        selected_theme = st.selectbox("Select new theme", THEMES,
                                      index=THEMES.index(current_theme) if current_theme in THEMES else 0,
                                      key=f"theme_sel_{endpoint_prefix}")
        if st.button("Change Theme", type="primary", icon=":material/palette:", key=f"theme_btn_{endpoint_prefix}"):
            post_edit(endpoint_prefix, doc_id,
                      [{"section": "theme", "item_name": "", "field": "", "new_value": selected_theme}],
                      invalidate_fn, f"Theme changed to **{selected_theme}**.")


def add_project_section(doc_id, endpoint_prefix, invalidate_fn):
    today = pendulum.today().date()
    projects = fetch_projects()
    if not projects:
        st.info("No saved project analyses found.")
        return
    selected = st.selectbox("Select project to add", projects, key=f"proj_sel_{endpoint_prefix}")
    resume_item = (fetch_project_info(selected).get("analysis") or {}).get("resume_item") or {}
    if resume_item:
        with st.expander("Current project info", expanded=True):
            if resume_item.get("summary"):
                st.markdown(f"**Summary:** {resume_item['summary']}")
            if resume_item.get("highlights"):
                st.markdown("**Highlights:**")
                for h in resume_item["highlights"]:
                    st.markdown(f"- {h}")
    with st.form(f"add_proj_{endpoint_prefix}", clear_on_submit=True):
        ov_summary    = st.text_area("Override summary (optional)", height=80)
        ov_highlights = st.text_area("Override highlights (optional, one per line)", height=80)
        c1, c2 = st.columns(2)
        with c1:
            ov_start = st.date_input("Start date", value=None, help="Leave blank to use project default", key=f"add_start_{endpoint_prefix}")
        with c2:
            ov_end = st.date_input("End date", value=None, help="Select today to use 'present'", key=f"add_end_{endpoint_prefix}")
        if st.form_submit_button("Add Project", type="primary", icon=":material/add:"):
            highlights = [h.strip() for h in ov_highlights.splitlines() if h.strip()]
            start_str = ov_start.strftime("%Y-%m") if ov_start else ""
            end_str = "present" if ov_end == today else (ov_end.strftime("%Y-%m") if ov_end else "")
            payload = {k: v for k, v in {"summary": ov_summary, "start_date": start_str, "end_date": end_str}.items() if v}
            if highlights:
                payload["highlights"] = highlights
            res = requests.post(f"{API_BASE}/{endpoint_prefix}/{doc_id}/add/project/{selected}", json=payload or None, timeout=15)
            if res.ok:
                invalidate_fn()
                st.session_state.pop("projects_cache", None)
                st.success(res.json().get("status", "Project added."))
                st.rerun()
            else:
                st.error(api_error(res))


def modify_entries_section(doc_id, rd, section, item_key, field_options, endpoint_prefix, invalidate_fn):
    today = pendulum.today().date()
    entries = rd.get(section) or []
    if not entries:
        st.info(f"No {section} entries in this document yet.")
        return
    entry_names = [e.get(item_key, "") for e in entries if e.get(item_key)]
    selected = st.selectbox(f"Select {section} entry", entry_names, key=f"mod_{section}_sel_{endpoint_prefix}")
    entry_data = next((e for e in entries if e.get(item_key) == selected), None)
    if not entry_data:
        return
    with st.container(border=True):
        attribute = st.selectbox("Field to modify", field_options, key=f"mod_{section}_attr_{endpoint_prefix}")
        current_value = entry_data.get(attribute, "")
        if attribute == "highlights":
            st.markdown("**Current highlights:**")
            for h in (current_value or []):
                st.markdown(f"- {h}")
        else:
            st.markdown(f"**Current value:** {current_value}")
        with st.form(f"mod_{section}_form_{endpoint_prefix}", clear_on_submit=False):
            if attribute == "highlights":
                raw = st.text_area("New highlights (one per line)", value="\n".join(current_value or []))
                new_value = "\n".join([h.strip() for h in raw.splitlines() if h.strip()])
            elif attribute in ("summary",):
                new_value = st.text_area(f"New {attribute}", value=str(current_value or ""), height=120)
            elif attribute in ("start_date", "end_date"):
                try:
                    default_date = pendulum.parse(str(current_value)).date() if current_value and current_value != "present" else today
                except Exception:
                    default_date = today
                picked = st.date_input(f"New {attribute}", value=default_date, key=f"mod_{section}_date_{attribute}_{endpoint_prefix}")
                new_value = "present" if (attribute == "end_date" and picked == today) else picked.strftime("%Y-%m")
            else:
                new_value = st.text_input(f"New {attribute}", value=str(current_value or ""))
            if st.form_submit_button(f"Update {attribute}", type="primary", icon=":material/update:"):
                post_edit(endpoint_prefix, doc_id,
                          [{"section": section, "item_name": selected, "field": attribute, "new_value": new_value}],
                          invalidate_fn, f"Updated **{attribute}** for '{selected}'.")


def download_section(doc_id, endpoint_prefix, dl_key):
    fmt = st.selectbox("Format", FORMATS, key=f"{dl_key}_fmt")
    if st.button("Render & Prepare Download", type="primary", icon=":material/construction:", key=f"{dl_key}_btn"):
        with st.spinner("Rendering...", show_time=True):
            res = requests.post(f"{API_BASE}/{endpoint_prefix}/{doc_id}/render/{fmt}", timeout=60)
        if res.ok:
            st.session_state[f"{dl_key}_bytes"] = res.content
            st.session_state[f"{dl_key}_rendered"] = fmt
        else:
            st.error(api_error(res))
    if st.session_state.get(f"{dl_key}_bytes") and st.session_state.get(f"{dl_key}_rendered") == fmt:
        ext = FILE_EXTS[fmt]
        st.download_button(f"Download {endpoint_prefix}.{ext}", data=st.session_state[f"{dl_key}_bytes"],
                           file_name=f"{endpoint_prefix}.{ext}", mime=MIME_TYPES[fmt],
                           type="primary", icon=":material/download:")


def delete_doc_section(existing, endpoint_prefix, key):
    if not existing:
        st.warning(f"No saved {endpoint_prefix}s found.")
    else:
        selected = st.selectbox(f"Select {endpoint_prefix} to delete", existing,
                                format_func=lambda x: x.rsplit("_", 1)[0].replace("_", " "),
                                key=f"{key}_select")
        if st.button(f"Delete {endpoint_prefix.capitalize()}", type="primary",
                     icon=":material/delete:", key=f"{key}_btn"):
            res = requests.delete(f"{API_BASE}/{endpoint_prefix}/{selected}", timeout=10)
            if res.ok:
                st.success(f"Deleted **{selected.rsplit('_', 1)[0].replace('_', ' ')}**.")
                st.rerun()
            else:
                st.error(api_error(res))


def edit_connections_section(doc_id, pd_, endpoint_prefix, invalidate_fn):
    conn_names = [c.get("network", "") for c in (pd_.get("connections") or []) if c.get("network")]
    action = st.segmented_control("Connections", ["➕ Add Connection", "🗑️ Remove Connection"],
                                  label_visibility="hidden", key="conn_action")
    if action == "➕ Add Connection":
        with st.form("add_connection_form", clear_on_submit=True):
            network  = st.selectbox("Network", SOCIAL_NETWORKS)
            username = st.text_input("Username / handle")
            if st.form_submit_button("Add Connection", type="primary", icon=":material/add:"):
                post_edit(endpoint_prefix, doc_id,
                          [{"section": "connections", "item_name": network, "field": "username", "new_value": username}],
                          invalidate_fn, f"Added **{network}** connection.")
    elif action == "🗑️ Remove Connection":
        if not conn_names:
            st.info("No connections to remove.")
        else:
            with st.container(border=True):
                to_remove = st.selectbox("Select connection to remove", conn_names, key="conn_remove_sel")
                if st.button(f"Remove {to_remove}", type="primary", icon=":material/delete:", key="conn_remove_btn"):
                    post_edit(endpoint_prefix, doc_id,
                              [{"section": "connections", "item_name": to_remove, "field": "delete", "new_value": ""}],
                              invalidate_fn, f"Removed **{to_remove}**.")


def add_education_section(doc_id, invalidate_fn):
    today = pendulum.today().date()
    with st.form("add_education_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            institution = st.text_input("Institution *", placeholder="e.g., University of British Columbia")
            area = st.text_input("Area of Study *", placeholder="e.g., Computer Science")
            degree = st.text_input("Degree", placeholder="e.g., BSc")
            gpa = st.text_input("GPA", placeholder="e.g., 3.8")
        with c2:
            start = st.date_input("Start date", value=None, key="edu_add_start")
            end = st.date_input("End date", value=None, help="Select today for 'present'", key="edu_add_end")
            location = st.text_input("Location", placeholder="e.g., Kelowna, BC")
        highlights = st.text_area("Highlights (one per line)", height=100, key="edu_add_highlights")
        if st.form_submit_button("Add Education", type="primary", icon=":material/add:"):
            if not institution.strip() or not area.strip():
                st.warning("Institution and Area are required.", icon=":material/warning:")
            else:
                payload = {"institution": institution.strip(), "area": area.strip()}
                if degree.strip():
                    payload["degree"] = degree.strip()
                if gpa.strip():
                    payload["gpa"] = gpa.strip()
                if location.strip():
                    payload["location"] = location.strip()
                if start:
                    payload["start_date"] = start.strftime("%Y-%m")
                if end:
                    payload["end_date"] = "present" if end == today else end.strftime("%Y-%m")
                hl = [h.strip() for h in highlights.splitlines() if h.strip()]
                if hl:
                    payload["highlights"] = hl
                res = requests.post(f"{API_BASE}/resume/{doc_id}/add/education", json=payload, timeout=15)
                if res.ok:
                    invalidate_fn()
                    st.session_state["_flash_success"] = "Education entry added."
                    st.rerun()
                else:
                    st.error(api_error(res))


def remove_education_section(doc_id, rd, invalidate_fn):
    entries = rd.get("education") or []
    if not entries:
        st.info("No education entries to remove.")
        return
    names = [e.get("institution", "") for e in entries if e.get("institution")]
    selected = st.selectbox("Select education to remove", names, key="edu_remove_sel")
    if st.button(f"Remove {selected}", type="primary", icon=":material/delete:", key="edu_remove_btn"):
        res = requests.delete(f"{API_BASE}/resume/{doc_id}/education/{selected}", timeout=10)
        if res.ok:
            invalidate_fn()
            st.session_state["_flash_success"] = f"Removed **{selected}**."
            st.rerun()
        else:
            st.error(api_error(res))


def add_experience_section(doc_id, invalidate_fn):
    today = pendulum.today().date()
    with st.form("add_experience_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            company = st.text_input("Company *", placeholder="e.g., Acme Corp")
            position = st.text_input("Position", placeholder="e.g., Software Engineer")
        with c2:
            start = st.date_input("Start date", value=None, key="exp_add_start")
            end = st.date_input("End date", value=None, help="Select today for 'present'", key="exp_add_end")
        location = st.text_input("Location", placeholder="e.g., Vancouver, BC")
        highlights = st.text_area("Highlights (one per line)", height=100, key="exp_add_highlights")
        if st.form_submit_button("Add Experience", type="primary", icon=":material/add:"):
            if not company.strip():
                st.warning("Company is required.", icon=":material/warning:")
            else:
                payload = {"company": company.strip()}
                if position.strip():
                    payload["position"] = position.strip()
                if location.strip():
                    payload["location"] = location.strip()
                if start:
                    payload["start_date"] = start.strftime("%Y-%m")
                if end:
                    payload["end_date"] = "present" if end == today else end.strftime("%Y-%m")
                hl = [h.strip() for h in highlights.splitlines() if h.strip()]
                if hl:
                    payload["highlights"] = hl
                res = requests.post(f"{API_BASE}/resume/{doc_id}/add/experience", json=payload, timeout=15)
                if res.ok:
                    invalidate_fn()
                    st.session_state["_flash_success"] = "Experience entry added."
                    st.rerun()
                else:
                    st.error(api_error(res))


def remove_experience_section(doc_id, rd, invalidate_fn):
    entries = rd.get("experience") or []
    if not entries:
        st.info("No experience entries to remove.")
        return
    names = [e.get("company", "") for e in entries if e.get("company")]
    selected = st.selectbox("Select experience to remove", names, key="exp_remove_sel")
    if st.button(f"Remove {selected}", type="primary", icon=":material/delete:", key="exp_remove_btn"):
        res = requests.delete(f"{API_BASE}/resume/{doc_id}/experience/{selected}", timeout=10)
        if res.ok:
            invalidate_fn()
            st.session_state["_flash_success"] = f"Removed **{selected}**."
            st.rerun()
        else:
            st.error(api_error(res))