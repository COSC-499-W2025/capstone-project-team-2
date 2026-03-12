"""Project Upload page for ingesting local project artifacts.

Private-mode only page that supports two upload paths:
1) direct ZIP upload
2) local folder -> in-memory ZIP -> upload

Both paths end in the same backend contract:
- POST /projects/upload
- GET  /analyze
"""

import streamlit as st
import requests
import zipfile
import io
from pathlib import Path
from html import escape
import sys


# Allow this page module to import shared frontend utilities.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.web.mode import render_page_header, require_private_mode
from src.web.streamlit_helpers import API_BASE

# Project upload is private-only because it mutates stored analysis data.
require_private_mode("Project Upload")

render_page_header(
    "Project Upload",
    "Analyze a project by uploading a ZIP file or using a local folder path.",
)


def _render_upload_intro() -> None:
    """Render top-level workflow framing inspired by sidebar structure."""
    st.markdown(
        """
        <div class="upload-hero">
            <h3>Workflow</h3>
            <p>Choose a source, analyze the project, and review extracted insights below.</p>
            <div class="upload-chip-row">
                <span class="upload-chip">1. Select Source</span>
                <span class="upload-chip">2. Analyze</span>
                <span class="upload-chip">3. Review Metrics</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_chip_list(title: str, values: list[str]) -> None:
    """Render a compact chip list for insight metadata."""
    safe_values = [escape(v) for v in values if str(v).strip()]
    with st.container(border=False):
        st.markdown(f"<div class='insight-group'><h4>{escape(title)}</h4>", unsafe_allow_html=True)
        if not safe_values:
            st.caption("None detected")
        else:
            chips = "".join(f"<span class='upload-chip'>{v}</span>" for v in safe_values)
            st.markdown(f"<div class='upload-chip-row'>{chips}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def display_project_insights(project_name: str) -> None:
    """Fetch and render the newest insight record for an analyzed project.

    Args:
        project_name: Name returned by upload/analyze API flow.

    Returns:
        None. Renders insight UI blocks directly.
    """
    insights_resp = requests.get(f"{API_BASE}/insights/projects")
    if insights_resp.status_code != 200:
        st.warning("Analysis complete, but couldn't load project insights.")
        return

    all_insights = insights_resp.json()
    matches = [i for i in all_insights if i.get("project_name") == project_name]
    if not matches:
        st.warning("Analysis complete, but no insight record was found.")
        return

    insight = matches[-1]  # most recent matching project analysis

    st.success(f"Analysis complete for **{project_name}**.")
    with st.container(border=True):
        st.markdown("<p class='upload-section-title'>Insight Overview</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Project Type", insight.get("project_type", "—").capitalize())
        col2.metric("Duration Estimate", insight.get("duration_estimate", "—"))
        col3.metric("Skills Detected", insight.get("stats", {}).get("skill_count", 0))

    if insight.get("summary"):
        with st.container(border=True):
            st.markdown("<p class='upload-section-title'>Summary</p>", unsafe_allow_html=True)
            st.write(insight["summary"])

    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        _render_chip_list("Languages", insight.get("languages", []))
        _render_chip_list("Frameworks", insight.get("frameworks", []))

    with col_right:
        _render_chip_list("Skills", insight.get("skills", []))

    file_analysis = insight.get("file_analysis", {})
    if file_analysis:
        with st.container(border=True):
            st.markdown("<p class='upload-section-title'>File Analysis</p>", unsafe_allow_html=True)
            fa_col1, fa_col2, fa_col3 = st.columns(3)
            fa_col1.metric("Total Files", file_analysis.get("file_count", "—"))
            fa_col2.metric("Total Size", f"{file_analysis.get('total_size_bytes', 0):,} bytes")
            fa_col3.metric("Avg File Size", f"{file_analysis.get('average_size_bytes', 0):,} bytes")

    contributors = insight.get("contributors", {})
    if contributors:
        with st.container(border=True):
            st.markdown("<p class='upload-section-title'>Contributors</p>", unsafe_allow_html=True)
            chips = "".join(
                f"<span class='upload-chip'>{escape(name)}: {count}</span>"
                for name, count in contributors.items()
            )
            st.markdown(f"<div class='upload-chip-row'>{chips}</div>", unsafe_allow_html=True)


def _render_zip_upload() -> None:
    """Render ZIP-file upload analysis flow."""
    with st.container(border=True):
        st.markdown("<p class='section-title'>ZIP File</p>", unsafe_allow_html=True)
        st.caption("Point to a ZIP file. It will be uploaded directly before analysis.")
        input_col, _ = st.columns([2.25, 2.75], gap="large")
        with input_col:
            uploaded_file = st.file_uploader(
                "Drag/drop ZIP or browse",
                type=["zip"],
                help="Only .zip files are supported",
            )

        input_col, _ = st.columns([2.25, 2.75], gap="large")
        with input_col:
            zip_path = st.text_input(
                "ZIP file path (optional)",
                placeholder="e.g. C:\\Users\\you\\projects\\snapshot.zip  or  /home/you/projects/snapshot.zip",
            )

        if uploaded_file is not None:
            st.info(f"Ready: `{uploaded_file.name}`")

        action_col, _ = st.columns([1.1, 3.9], gap="small")
        with action_col:
            run_zip = st.button("Analyze ZIP", type="primary", key="analyze_zip_btn", use_container_width=True)

        if not run_zip:
            return

        if uploaded_file is not None:
            with st.spinner("Uploading and analyzing..."):
                upload_resp = requests.post(
                    f"{API_BASE}/projects/upload",
                    files={"upload_file": (uploaded_file.name, uploaded_file, "application/zip")},
                )

                if upload_resp.status_code == 200:
                    project_name = upload_resp.json().get("project_name", "Unknown")
                    analyze_resp = requests.get(f"{API_BASE}/analyze")

                    if analyze_resp.status_code == 200:
                        display_project_insights(project_name)
                    else:
                        st.error(f"Analysis failed: {analyze_resp.json().get('detail', 'Unknown error')}")
                else:
                    st.error(f"Upload failed: {upload_resp.json().get('detail', 'File must be a valid ZIP')}")
            return

        if not zip_path.strip():
            st.warning("Upload a ZIP or enter a ZIP file path.")
            return

        path = Path(zip_path.strip())
        if not path.exists():
            st.error(f"Path does not exist: `{path}`")
            return
        if not path.is_file():
            st.error("Path must be a ZIP file.")
            return
        if path.suffix.lower() != ".zip":
            st.error("File must have a .zip extension.")
            return

        with st.spinner("Uploading and analyzing..."):
            with path.open("rb") as fh:
                upload_resp = requests.post(
                    f"{API_BASE}/projects/upload",
                    files={"upload_file": (path.name, fh, "application/zip")},
                )

            if upload_resp.status_code == 200:
                project_name = upload_resp.json().get("project_name", path.stem or "Unknown")
                analyze_resp = requests.get(f"{API_BASE}/analyze")

                if analyze_resp.status_code == 200:
                    display_project_insights(project_name)
                else:
                    st.error(f"Analysis failed: {analyze_resp.json().get('detail', 'Unknown error')}")
            else:
                st.error(f"Upload failed: {upload_resp.json().get('detail', 'File must be a valid ZIP')}")


def _render_folder_upload() -> None:
    """Render local-folder analysis flow."""
    with st.container(border=True):
        st.markdown("<p class='section-title'>Local Folder Path</p>", unsafe_allow_html=True)
        st.caption("Point to a local directory. It will be zipped automatically before analysis.")

        input_col, _ = st.columns([2.25, 2.75], gap="large")
        with input_col:
            folder_zip = st.file_uploader(
                "Drag/drop ZIP snapshot (optional)",
                type=["zip"],
                help="Optional alternative: drop a ZIP instead of entering a folder path.",
                key="folder_alt_zip_uploader",
            )

        input_col, _ = st.columns([2.25, 2.75], gap="large")
        with input_col:
            folder_path = st.text_input(
                "Project folder path",
                placeholder="e.g. C:\\Users\\you\\projects\\my-app  or  /home/you/projects/my-app",
            )

        action_col, _ = st.columns([1.1, 3.9], gap="small")
        with action_col:
            run_folder = st.button("Analyze Folder", type="primary", key="analyze_folder_btn", use_container_width=True)

        if not run_folder:
            return

        # Allow same drag/drop behavior in this section via optional ZIP upload.
        if folder_zip is not None:
            with st.spinner("Uploading and analyzing..."):
                upload_resp = requests.post(
                    f"{API_BASE}/projects/upload",
                    files={"upload_file": (folder_zip.name, folder_zip, "application/zip")},
                )
                if upload_resp.status_code == 200:
                    project_name = upload_resp.json().get("project_name", "Unknown")
                    analyze_resp = requests.get(f"{API_BASE}/analyze")
                    if analyze_resp.status_code == 200:
                        display_project_insights(project_name)
                    else:
                        st.error(f"Analysis failed: {analyze_resp.json().get('detail', 'Unknown error')}")
                else:
                    st.error(f"Upload failed: {upload_resp.json().get('detail', 'File must be a valid ZIP')}")
            return

        if not folder_path.strip():
            st.warning("Please enter a folder path.")
            return

        path = Path(folder_path.strip())
        if not path.exists():
            st.error(f"Path does not exist: `{path}`")
            return
        if not path.is_dir():
            st.error("Path must be a folder (directory), not a file.")
            return

        with st.spinner("Zipping folder and analyzing..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in path.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(path.parent))
            zip_buffer.seek(0)

            zip_name = f"{path.name}.zip"
            upload_resp = requests.post(
                f"{API_BASE}/projects/upload",
                files={"upload_file": (zip_name, zip_buffer, "application/zip")},
            )

            if upload_resp.status_code == 200:
                project_name = upload_resp.json().get("project_name", path.name)
                analyze_resp = requests.get(f"{API_BASE}/analyze")

                if analyze_resp.status_code == 200:
                    display_project_insights(project_name)
                else:
                    st.error(f"Analysis failed: {analyze_resp.json().get('detail', 'Unknown error')}")
            else:
                st.error(f"Upload failed: {upload_resp.json().get('detail', 'Unknown error')}")


_render_upload_intro()

st.session_state.setdefault("upload_source_mode", "zip")

source_mode = st.session_state["upload_source_mode"]
with st.container(border=True):
    active_source_label = "Upload ZIP" if source_mode == "zip" else "Local Folder Path"
    title_col, chip_col = st.columns([5, 2], gap="small")
    with title_col:
        st.markdown("**Source**")
    with chip_col:
        st.markdown(
            f"<div class='chip-align-right'><span class='page-chip'>Active: {escape(active_source_label)}</span></div>",
            unsafe_allow_html=True,
        )
    st.caption("Choose where your project files come from before analysis.")
    left_col, right_col, _ = st.columns([1.15, 1.35, 3.5], gap="small")
    with left_col:
        if st.button(
            "Upload ZIP",
            key="upload_seg_zip",
            type="primary" if source_mode == "zip" else "secondary",
            icon=":material/folder_zip:",
            use_container_width=True,
        ):
            st.session_state["upload_source_mode"] = "zip"
            st.rerun()
    with right_col:
        if st.button(
            "Local Folder Path",
            key="upload_seg_folder",
            type="primary" if source_mode == "folder" else "secondary",
            icon=":material/folder:",
            use_container_width=True,
        ):
            st.session_state["upload_source_mode"] = "folder"
            st.rerun()

if st.session_state["upload_source_mode"] == "zip":
    _render_zip_upload()
else:
    _render_folder_upload()
