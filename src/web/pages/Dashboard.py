"""Dashboard page for timeline, heatmap, and top project highlights.

This page is intentionally data-first:
- It tries live API data first (`/insights/projects`) so users see current analysis.
- It falls back to local `project_insights.json` for offline/demo reliability.
- It derives lightweight portfolio signals (skills trend, activity buckets, top projects)
  directly from saved insight payloads.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.web.mode import render_page_header
from src.web.streamlit_helpers import API_BASE

PROJECT_INSIGHTS_PATH = Path(__file__).resolve().parents[3] / "User_config_files" / "project_insights.json"
ACTIVITY_TYPES = ("code", "test", "design", "document", "other")

# File-type heuristics used to infer activity categories from project trees.
CODE_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rb", ".php", ".swift", ".kt", ".rs", ".sql", ".sh",
}
TEST_HINTS = ("/test/", "/tests/", "_test.", "test_", "spec.")
DESIGN_HINTS = ("/design", "/ui", "/ux", "figma", "sketch", "wireframe", "mockup")
DOC_HINTS = ("/doc", "/docs", "readme", "report", "notes")
DESIGN_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".fig"}
DOC_EXTENSIONS = {".md", ".txt", ".pdf", ".doc", ".docx", ".ppt", ".pptx"}


def _parse_dt(value: Any) -> datetime | None:
    """Parse datetime values found in insight payloads.

    Supports both:
    - ISO timestamps (API output, e.g. `2026-03-08T10:00:00+00:00`)
    - Legacy flat timestamps (e.g. `2026-03-08 10:00:00`)

    Args:
        value: Raw timestamp value from project insight payloads.

    Returns:
        A parsed datetime object, or ``None`` when parsing fails.
    """
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _iter_file_nodes(node: Dict[str, Any], prefix: str = "") -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield ``(path, node)`` for all non-directory nodes in a hierarchy tree.

    The hierarchy payload is nested. This helper flattens it so activity
    classification can operate on individual files.

    Args:
        node: Current hierarchy node from project insight payload.
        prefix: Path prefix accumulated from parent nodes.

    Returns:
        An iterator of ``(path, node)`` tuples for file-like nodes.
    """
    name = str(node.get("name", "") or "")
    current = f"{prefix}/{name}" if prefix else name
    node_type = str(node.get("type", "")).upper()
    children = node.get("children") or []

    if node_type and node_type != "DIR":
        yield current, node
    for child in children:
        if isinstance(child, dict):
            yield from _iter_file_nodes(child, current)


def _classify_activity(path: str, node: Dict[str, Any]) -> str:
    """Classify file activity into one of the dashboard activity buckets.

    Precedence is intentional:
    1) test hints
    2) design hints
    3) document hints
    4) code extensions/types
    5) fallback to `other`

    Args:
        path: File path used for hint/extension checks.
        node: File node payload containing optional type metadata.

    Returns:
        One of ``code/test/design/document/other``.
    """
    lower_path = path.lower()
    ext = Path(lower_path).suffix
    node_type = str(node.get("type", "")).lower()

    if any(hint in lower_path for hint in TEST_HINTS):
        return "test"
    if any(hint in lower_path for hint in DESIGN_HINTS) or ext in DESIGN_EXTENSIONS:
        return "design"
    if any(hint in lower_path for hint in DOC_HINTS) or ext in DOC_EXTENSIONS:
        return "document"
    if ext in CODE_EXTENSIONS or node_type in {e.removeprefix(".") for e in CODE_EXTENSIONS}:
        return "code"
    return "other"


def _project_score(project: Dict[str, Any]) -> float:
    """Compute a stable ranking score from contribution and skill signals.

    Weighting keeps contribution volume as the dominant factor while still
    rewarding contribution share and skill breadth:
    ``score = (top_count * 100) + top_pct + (skill_count * 3)``

    Args:
        project: Project insight record.

    Returns:
        A numeric ranking score used for sorting top projects.
    """
    stats = project.get("stats") or {}
    top_count = int(stats.get("top_contribution_count") or 0)
    top_pct = float(stats.get("top_contribution_percentage") or 0.0)
    skill_count = int(stats.get("skill_count") or len(project.get("skills") or []))
    return (top_count * 100.0) + top_pct + (skill_count * 3.0)


@st.cache_data(ttl=20)
def _load_projects() -> Tuple[List[Dict[str, Any]], str]:
    """Load projects from API with local JSON fallback.

    Returns:
        tuple[list[dict], str]:
            - projects payload
            - source label (`API`, `local file`, or `none`)
    """
    try:
        resp = requests.get(f"{API_BASE}/insights/projects", timeout=8)
        if resp.ok and isinstance(resp.json(), list):
            return resp.json(), "API"
    except requests.RequestException:
        pass

    if PROJECT_INSIGHTS_PATH.exists():
        try:
            payload = json.loads(PROJECT_INSIGHTS_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload, "local file"
        except (OSError, json.JSONDecodeError):
            pass

    return [], "none"


def _build_skills_project_timeline(projects: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build project-level timeline rows for skill count over time.

    Each row represents one analyzed project at one date with the number of
    extracted skills.

    Args:
        projects: List of project insight records.

    Returns:
        A dataframe with ``date``, ``project_name``, and ``skill_count`` columns.
    """
    rows: List[Dict[str, Any]] = []
    for project in projects:
        dt = _parse_dt(project.get("analyzed_at"))
        if dt is None:
            continue
        skills = project.get("skills") or []
        rows.append(
            {
                "date": dt.date(),
                "project_name": project.get("project_name", "Unknown"),
                "skill_count": len(skills),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("date")


def _build_skill_frequency_timeline(projects: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build month-by-skill counts for skill exercise timeline visualization.

    Output shape is a pivot table:
    - index: month (`YYYY-MM`)
    - columns: skill names
    - values: occurrence count across projects in that month

    Args:
        projects: List of project insight records.

    Returns:
        A month-by-skill pivot dataframe.
    """
    rows: List[Dict[str, Any]] = []
    for project in projects:
        dt = _parse_dt(project.get("analyzed_at"))
        if dt is None:
            continue
        month = dt.strftime("%Y-%m")
        for skill in sorted(set(project.get("skills") or [])):
            rows.append({"month": month, "skill": skill, "count": 1})
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    grouped = df.groupby(["month", "skill"], as_index=False)["count"].sum()
    pivot = grouped.pivot(index="month", columns="skill", values="count").fillna(0).astype(int)
    return pivot.sort_index()


def _build_activity_heatmap(projects: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build month x activity heatmap matrix based on hierarchy files.

    For each project, file nodes are bucketed into:
    ``code/test/design/document/other`` and aggregated by analyzed month.

    Args:
        projects: List of project insight records.

    Returns:
        An activity-by-month pivot dataframe.
    """
    rows: List[Dict[str, Any]] = []
    for project in projects:
        dt = _parse_dt(project.get("analyzed_at"))
        if dt is None:
            continue
        month = dt.strftime("%Y-%m")
        counts = Counter()
        hierarchy = project.get("hierarchy")
        if isinstance(hierarchy, dict):
            for file_path, node in _iter_file_nodes(hierarchy):
                counts[_classify_activity(file_path, node)] += 1

        for activity in ACTIVITY_TYPES:
            rows.append({"activity": activity, "month": month, "count": counts.get(activity, 0)})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index="activity", columns="month", values="count", aggfunc="sum", fill_value=0)
    return pivot.reindex(ACTIVITY_TYPES).sort_index(axis=1)


def _render_top_projects(projects: List[Dict[str, Any]]) -> None:
    """Render top-3 project cards using contribution-based ranking.

    Args:
        projects: List of project insight records.

    Returns:
        None. Renders Streamlit components directly.
    """
    ranked = sorted(projects, key=_project_score, reverse=True)[:3]
    st.subheader("Top 3 Projects")
    if not ranked:
        st.info("No projects are available yet.")
        return

    cols = st.columns(3)
    for idx, project in enumerate(ranked):
        stats = project.get("stats") or {}
        with cols[idx]:
            with st.container(border=True):
                st.markdown(f"**{project.get('project_name', 'Unknown Project')}**")
                st.caption(project.get("project_type", "unknown").title())
                st.write((project.get("summary") or "No summary available.")[:220])
                st.caption(
                    "Top contribution: "
                    f"{stats.get('top_contribution_count', 0)} "
                    f"{stats.get('contribution_metric', 'items')}"
                )
                st.caption(f"Skills: {len(project.get('skills') or [])}")


def render_page() -> None:
    """Render the dashboard page.

    Public mode stays read-only. Private mode enables skill selection controls.

    Returns:
        None. Renders dashboard sections directly.
    """
    mode = render_page_header(
        "Dashboard",
        "Timeline of skills, activity heatmap, and top project highlights.",
    )
    st.markdown(
        """
        <div class="page-hero">
            <h3>Dashboard Workspace</h3>
            <p>Track skill growth, activity volume, and top project impact from analyzed insights.</p>
            <div class="page-chip-row">
                <span class="page-chip">Timeline</span>
                <span class="page-chip">Heatmap</span>
                <span class="page-chip">Top Projects</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    projects, source = _load_projects()
    st.caption(f"Data source: {source}")

    if not projects:
        st.warning("No project insights found. Analyze at least one project to populate the dashboard.")
        return

    project_count = len(projects)
    unique_skills = sorted({s for p in projects for s in (p.get("skills") or [])})
    parsed_dts = [dt for p in projects if (dt := _parse_dt(p.get("analyzed_at"))) is not None]
    latest_dt = max(parsed_dts) if parsed_dts else None

    m1, m2, m3 = st.columns(3)
    m1.metric("Projects", f"{project_count}")
    m2.metric("Unique Skills", f"{len(unique_skills)}")
    m3.metric("Latest Analysis", latest_dt.strftime("%Y-%m-%d") if latest_dt else "Unknown")

    with st.container(border=True):
        st.markdown("<p class='section-title'>Skills Timeline</p>", unsafe_allow_html=True)
        project_timeline = _build_skills_project_timeline(projects)
        if project_timeline.empty:
            st.info("No timestamped skill data is available yet.")
        else:
            st.line_chart(project_timeline.set_index("date")["skill_count"], height=250)

            skill_timeline = _build_skill_frequency_timeline(projects)
            if not skill_timeline.empty:
                candidates = sorted(skill_timeline.columns.tolist())
                if mode == "Public":
                    selected = candidates[: min(5, len(candidates))]
                    if selected:
                        st.area_chart(skill_timeline[selected], height=260)
                    st.caption("Public mode: fixed read-only skill view.")
                else:
                    selected = st.multiselect(
                        "Skills to track over time",
                        options=candidates,
                        default=candidates[: min(5, len(candidates))],
                    )
                    if selected:
                        st.area_chart(skill_timeline[selected], height=260)

    with st.container(border=True):
        st.markdown("<p class='section-title'>Activity Heatmap</p>", unsafe_allow_html=True)
        heatmap = _build_activity_heatmap(projects)
        if heatmap.empty:
            st.info("No hierarchy data is available for heatmap rendering.")
        else:
            st.dataframe(heatmap, use_container_width=True)

    _render_top_projects(projects)

if __name__ == "__main__":
    render_page()
