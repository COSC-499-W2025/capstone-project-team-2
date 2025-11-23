"""
project_insights
================

Utility helpers for persisting and querying analyzed project insights.

Responsibilities:
- Append analysis output (hierarchy, resume info, skills, contributors) to a JSON log
- Store derived file analysis stats alongside each project
- Provide chronological listings for projects and skill usage
- Rank projects based on contribution signals and surface top-ranked summaries
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

JsonEntry = Dict[str, Any]
ContributorData = Dict[str, Dict[str, Any]]
PathLike = Union[str, Path]

DEFAULT_STORAGE = Path("User_config_files/project_insights.json")


def _now_iso(ts: Optional[datetime] = None) -> str:
    """Return an ISO 8601 timestamp in UTC."""
    if ts is None:
        ts = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> None:
    """Ensure the parent directory for the provided file path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _stash_corrupted_file(path: Path) -> None:
    """Rename corrupted JSON logs so a clean file can be created safely."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(f"{path.name}.corrupt-{timestamp}")
    try:
        path.replace(backup)
    except Exception:
        # Nothing else we can do—leave the file in place.
        pass


def _read_entries(path: Path) -> List[JsonEntry]:
    """Read raw JSON entries from ``path`` and fall back to an empty list on error."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        _stash_corrupted_file(path)
        return []
    except json.JSONDecodeError:
        _stash_corrupted_file(path)
        return []
    except OSError:
        return []


def _write_entries(path: Path, entries: Sequence[JsonEntry]) -> None:
    """Serialize entries with indentation to aid manual inspection."""
    _ensure_dir(path)
    path.write_text(json.dumps(list(entries), indent=2), encoding="utf-8")


def _normalize_contributors(contributors: Optional[ContributorData]) -> ContributorData:
    """Ensure every contributor entry contains a ``file_count`` to help ranking later."""
    if not contributors:
        return {}
    out: ContributorData = {}
    for name, data in contributors.items():
        data = dict(data or {})
        count = data.get("file_count")
        if count is None:
            count = len(data.get("files_owned", []))
        try:
            data["file_count"] = int(count)
        except Exception:
            data["file_count"] = 0
        out[name] = data
    return out


def _summarize_contributors(contributors: ContributorData) -> Dict[str, Any]:
    """Build aggregate stats for contributor information."""
    if not contributors:
        return {
            "contributors": 0,
            "total_file_contributions": 0,
            "top_contributor": None,
            "top_contribution_count": 0,
        }
    total = 0
    top_name: Optional[str] = None
    top_count = -1
    for name, info in contributors.items():
        c = int(info.get("file_count", 0))
        total += c
        if c > top_count:
            top_count = c
            top_name = name
    return {
        "contributors": len(contributors),
        "total_file_contributions": total,
        "top_contributor": top_name,
        "top_contribution_count": max(top_count, 0),
    }


def _parse_analyzed_at(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp, falling back to a minimal UTC datetime on error."""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            # Assume UTC if no timezone is present.
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # Extremely defensive: if the stored timestamp is malformed,
        # push it to the beginning of the timeline.
        return datetime.min.replace(tzinfo=timezone.utc)


def _flatten_file_nodes(hierarchy: JsonEntry) -> List[JsonEntry]:
    """
    Traverse a hierarchy tree emitted by ``FileMetadataExtractor`` and return file nodes.
    Directory nodes (``type`` == ``DIR``) are ignored.
    """
    if not isinstance(hierarchy, dict):
        return []

    files: List[JsonEntry] = []
    stack: List[JsonEntry] = [hierarchy]

    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type", "")).upper()
        children = node.get("children") or []
        if node_type and node_type != "DIR":
            files.append(node)
        for child in children:
            if isinstance(child, dict):
                stack.append(child)

    return files


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def _compute_file_analysis(hierarchy: JsonEntry) -> Dict[str, Any]:
    """Derive file analysis stats to be stored with each insight."""
    files = _flatten_file_nodes(hierarchy)
    if not files:
        return {
            "file_count": 0,
            "total_size_bytes": 0,
            "average_size_bytes": 0,
            "file_types": {},
        }

    total_size = 0
    file_types: Dict[str, int] = {}
    largest = None
    newest_ts = None
    newest_file = None

    for node in files:
        size = _safe_int(node.get("size", 0))
        total_size += size
        ftype = str(node.get("type") or "FILE").upper()
        file_types[ftype] = file_types.get(ftype, 0) + 1
        if not largest or size > largest.get("size_bytes", 0):
            largest = {
                "name": node.get("name"),
                "type": ftype,
                "size_bytes": size,
            }
        modified = _parse_timestamp(node.get("modified"))
        if modified and (newest_ts is None or modified > newest_ts):
            newest_ts = modified
            newest_file = {
                "name": node.get("name"),
                "type": ftype,
                "modified": node.get("modified"),
            }

    file_count = len(files)
    analysis = {
        "file_count": file_count,
        "total_size_bytes": total_size,
        "average_size_bytes": total_size // file_count if file_count else 0,
        "file_types": file_types,
    }
    if largest:
        analysis["largest_file"] = largest
    if newest_file:
        analysis["newest_file"] = newest_file
    return analysis


@dataclass(frozen=True)
class ProjectInsight:
    """A single recorded project insight entry stored on disk."""
    id: str
    project_name: str
    summary: str
    analyzed_at: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    project_type: str = "unknown"
    detection_mode: str = "local"
    duration_estimate: str = "unavailable"
    hierarchy: JsonEntry = field(default_factory=dict)
    contributors: ContributorData = field(default_factory=dict)
    stats: JsonEntry = field(default_factory=dict)
    file_analysis: JsonEntry = field(default_factory=dict)

    def contribution_score(self, contributor: Optional[str] = None) -> int:
        """
        Determine the ranking score for this insight.

        Args:
            contributor: Optional contributor name to focus on. When supplied,
                use that contributor's ``file_count``. Otherwise rely on the
                pre-computed ``top_contribution_count``.
        """
        if contributor and contributor in self.contributors:
            try:
                return int(self.contributors[contributor].get("file_count", 0))
            except Exception:
                return 0
        try:
            return int(self.stats.get("top_contribution_count", 0))
        except Exception:
            return 0

    def to_dict(self) -> JsonEntry:
        return asdict(self)


def _entry_to_dataclass(entry: JsonEntry) -> ProjectInsight:
    """
    Convert a raw dict entry to ``ProjectInsight``, normalizing contributors
    and stats to keep behavior consistent across versions.
    """
    # Normalize contributors for older or external entries.
    raw_contributors = entry.get("contributors", {}) or {}
    contributors = _normalize_contributors(raw_contributors)

    # Normalize skills as a sorted list to ensure deterministic ordering.
    skills = sorted(entry.get("skills", []) or [])

    # Start from stored stats, but make a copy so we don't mutate the original dict.
    raw_stats = entry.get("stats") or {}
    stats: Dict[str, Any] = dict(raw_stats)

    # Ensure contributor-based stats are present.
    contrib_stats = _summarize_contributors(contributors)
    stats.setdefault("contributors", contrib_stats["contributors"])
    stats.setdefault("total_file_contributions", contrib_stats["total_file_contributions"])
    stats.setdefault("top_contributor", contrib_stats["top_contributor"])
    stats.setdefault("top_contribution_count", contrib_stats["top_contribution_count"])

    # Ensure skill_count is present.
    stats.setdefault("skill_count", len(skills))

    analyzed_at = entry.get("analyzed_at", _now_iso())
    hierarchy = entry.get("hierarchy", {})
    file_analysis = entry.get("file_analysis")
    if not isinstance(file_analysis, dict):
        file_analysis = _compute_file_analysis(hierarchy)

    return ProjectInsight(
        id=entry.get("id", str(uuid.uuid4())),
        project_name=str(entry.get("project_name", "unknown")),
        summary=entry.get("summary", ""),
        analyzed_at=analyzed_at,
        languages=sorted(entry.get("languages", []) or []),
        frameworks=sorted(entry.get("frameworks", []) or []),
        skills=skills,
        project_type=entry.get("project_type", "unknown"),
        detection_mode=entry.get("detection_mode", "local"),
        duration_estimate=str(entry.get("duration_estimate", "unavailable")),
        hierarchy=hierarchy,
        contributors=contributors,
        stats=stats,
        file_analysis=file_analysis,
    )


def record_project_insight(
    analysis: JsonEntry,
    *,
    storage_path: PathLike = DEFAULT_STORAGE,
    contributors: Optional[ContributorData] = None,
    analyzed_at: Optional[datetime] = None,
    insight_id: Optional[str] = None,
) -> ProjectInsight:
    """
    Append a new project insight entry derived from ``analysis``.

    Args:
        analysis: Dictionary produced by the analysis pipeline.
        storage_path: JSON file where insights should be persisted.
        contributors: Optional contributor mapping for ranking purposes.
        analyzed_at: Optional override for the timestamp.
        insight_id: Optional override for deterministic IDs during testing.
    """
    resume = analysis.get("resume_item") or {}
    project_root = analysis.get("project_root")
    project_name = resume.get("project_name")

    if not project_name and project_root:
        # Use the leaf name of the path if available; fallback to raw project_root.
        try:
            project_name = Path(project_root).name or project_root
        except Exception:
            project_name = project_root

    project_name = project_name or "unknown"

    normalized = _normalize_contributors(contributors)
    stats = _summarize_contributors(normalized)
    stats["skill_count"] = len(resume.get("skills", []))
    hierarchy = analysis.get("hierarchy", {})

    insight = ProjectInsight(
        id=insight_id or str(uuid.uuid4()),
        project_name=str(project_name),
        summary=resume.get("summary", ""),
        analyzed_at=_now_iso(analyzed_at),
        languages=sorted(resume.get("languages", []) or []),
        frameworks=sorted(resume.get("frameworks", []) or []),
        skills=sorted(resume.get("skills", []) or []),
        project_type=resume.get("project_type", "unknown"),
        detection_mode=resume.get("detection_mode", "local"),
        duration_estimate=str(analysis.get("duration_estimate", "unavailable")),
        hierarchy=hierarchy,
        contributors=normalized,
        stats=stats,
        file_analysis=_compute_file_analysis(hierarchy),
    )

    path = Path(storage_path)
    entries = _read_entries(path)
    entries.append(insight.to_dict())
    _write_entries(path, entries)

    return insight


def list_project_insights(storage_path: PathLike = DEFAULT_STORAGE) -> List[ProjectInsight]:
    """Return all stored insights ordered chronologically."""
    path = Path(storage_path)
    insights = (_entry_to_dataclass(e) for e in _read_entries(path))
    return sorted(insights, key=lambda i: _parse_analyzed_at(i.analyzed_at))


def rank_projects_by_contribution(
    *,
    storage_path: PathLike = DEFAULT_STORAGE,
    contributor: Optional[str] = None,
    top_n: Optional[int] = None,
) -> List[ProjectInsight]:
    """
    Sort stored insights by contribution score.

    Args:
        contributor: Optional contributor focus to score by that individual's impact.
        top_n: Optional cap on the returned list size. ``None`` returns all.
               Values <= 0 return an empty list.
    """
    ranked = sorted(
        list_project_insights(storage_path),
        key=lambda i: i.contribution_score(contributor),
        reverse=True,
    )
    if top_n is None:
        return ranked
    if top_n <= 0:
        return []
    return ranked[:top_n]


def list_skill_history(storage_path: PathLike = DEFAULT_STORAGE) -> List[Dict[str, Any]]:
    """
    Return a chronological list of the skills demonstrated per project.

    Each entry contains ``project_name``, ``skills``, and ``analyzed_at``.
    """
    return [
        {
            "project_name": insight.project_name,
            "skills": list(insight.skills),
            "analyzed_at": insight.analyzed_at,
            "skill_count": len(insight.skills),
        }
        for insight in list_project_insights(storage_path)
    ]


def summaries_for_top_ranked_projects(
    *,
    storage_path: PathLike = DEFAULT_STORAGE,
    contributor: Optional[str] = None,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """
    Return project summaries for the highest ranked projects.

    Args:
        contributor: Optional contributor name that influences ranking.
        top_n: Number of project summaries to include. Defaults to 3.
    """
    if top_n <= 0:
        return []
    ranked = rank_projects_by_contribution(
        storage_path=storage_path,
        contributor=contributor,
        top_n=top_n,
    )
    return [
        {
            "project_name": insight.project_name,
            "summary": insight.summary,
            "analyzed_at": insight.analyzed_at,
            "contributors": insight.stats.get("contributors"),
            "top_contribution_count": insight.stats.get("top_contribution_count"),
            "score": insight.contribution_score(contributor),
        }
        for insight in ranked
    ]


__all__ = [
    "ProjectInsight",
    "record_project_insight",
    "list_project_insights",
    "rank_projects_by_contribution",
    "list_skill_history",
    "summaries_for_top_ranked_projects",
]
