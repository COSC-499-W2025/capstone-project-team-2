import streamlit as st
import requests
import zipfile
import io
from pathlib import Path
import sys

# Add project root to path so we can import src.web.streamlit_helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.web.streamlit_helpers import API_BASE

st.title("Upload a Project")
st.write("Analyze your project by uploading a ZIP file or entering a local folder path.")


def display_project_insights(project_name: str):
    """Fetch and display the insight record for a just-analyzed project."""
    insights_resp = requests.get(f"{API_BASE}/insights/projects")
    if insights_resp.status_code != 200:
        st.warning("Analysis complete, but couldn't load project insights.")
        return

    all_insights = insights_resp.json()
    # Find the most recent insight matching this project name
    matches = [i for i in all_insights if i.get("project_name") == project_name]
    if not matches:
        st.warning("Analysis complete, but no insight record was found.")
        return

    insight = matches[-1]  # most recent

    st.success(f"🎉 Analysis complete for **{project_name}**!")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Project Type", insight.get("project_type", "—").capitalize())
    col2.metric("Duration Estimate", insight.get("duration_estimate", "—"))
    col3.metric("Skills Detected", insight.get("stats", {}).get("skill_count", 0))

    st.divider()

    if insight.get("summary"):
        st.subheader("📋 Summary")
        st.write(insight["summary"])

    col_left, col_right = st.columns(2)

    with col_left:
        languages = insight.get("languages", [])
        st.subheader("🧑‍💻 Languages")
        if languages:
            for lang in languages:
                st.markdown(f"- {lang}")
        else:
            st.caption("None detected")

        frameworks = insight.get("frameworks", [])
        st.subheader("🧩 Frameworks")
        if frameworks:
            for fw in frameworks:
                st.markdown(f"- {fw}")
        else:
            st.caption("None detected")

    with col_right:
        skills = insight.get("skills", [])
        st.subheader("⚡ Skills")
        if skills:
            for skill in skills:
                st.markdown(f"- {skill}")
        else:
            st.caption("None detected")

    file_analysis = insight.get("file_analysis", {})
    if file_analysis:
        st.divider()
        st.subheader("📁 File Analysis")
        fa_col1, fa_col2, fa_col3 = st.columns(3)
        fa_col1.metric("Total Files", file_analysis.get("file_count", "—"))
        fa_col2.metric("Total Size", f"{file_analysis.get('total_size_bytes', 0):,} bytes")
        fa_col3.metric("Avg File Size", f"{file_analysis.get('average_size_bytes', 0):,} bytes")

    contributors = insight.get("contributors", {})
    if contributors:
        st.divider()
        st.subheader("👥 Contributors")
        for name, count in contributors.items():
            st.markdown(f"- **{name}**: {count} file(s)")


tab_zip, tab_folder = st.tabs(["📦 Upload ZIP", "📁 Local Folder Path"])

# --- Tab 1: ZIP upload ---
with tab_zip:
    uploaded_file = st.file_uploader(
        "Drag and drop your project ZIP here",
        type=["zip"],
        help="Only .zip files are supported"
    )

    if uploaded_file is not None:
        st.success(f"✅ Ready: **{uploaded_file.name}**")

        if st.button("Analyze ZIP", type="primary"):
            with st.spinner("Uploading and analyzing..."):
                upload_resp = requests.post(
                    f"{API_BASE}/projects/upload",
                    files={"upload_file": (uploaded_file.name, uploaded_file, "application/zip")}
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

# --- Tab 2: Local folder path ---
with tab_folder:
    st.info("Enter the full path to your project folder on this machine.", icon="ℹ️")

    folder_path = st.text_input(
        "Project folder path",
        placeholder="e.g. C:\\Users\\you\\projects\\my-app  or  /home/you/projects/my-app"
    )

    if st.button("Analyze Folder", type="primary"):
        if not folder_path.strip():
            st.warning("Please enter a folder path.")
        else:
            path = Path(folder_path.strip())
            if not path.exists():
                st.error(f"Path does not exist: `{path}`")
            elif not path.is_dir():
                st.error("Path must be a folder (directory), not a file.")
            else:
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
                        files={"upload_file": (zip_name, zip_buffer, "application/zip")}
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