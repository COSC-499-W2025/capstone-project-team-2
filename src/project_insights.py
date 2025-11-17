"""
project_insights
================

Utility helpers for persisting and querying analyzed project insights.

Responsibilities:
- Append analysis output (hierarchy, résumé info, skills, contributors) to a JSON log
- Provide a chronological listing for projects
- Rank projects based on contribution signals
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

    # Ensure timestamp is timezone-aware and in UTC
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
        return data if isinstance(data, list) else []
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

    # Normalize skills as a list.
    skills = list(entry.get("skills", []) or [])

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

    return ProjectInsight(
        id=entry.get("id", str(uuid.uuid4())),
        project_name=str(entry.get("project_name", "unknown")),
        summary=entry.get("summary", ""),
        analyzed_at=analyzed_at,
        languages=list(entry.get("languages", []) or []),
        frameworks=list(entry.get("frameworks", []) or []),
        skills=skills,
        project_type=entry.get("project_type", "unknown"),
        detection_mode=entry.get("detection_mode", "local"),
        duration_estimate=str(entry.get("duration_estimate", "unavailable")),
        hierarchy=entry.get("hierarchy", {}),
        contributors=contributors,
        stats=stats,
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
        hierarchy=analysis.get("hierarchy", {}),
        contributors=normalized,
        stats=stats,
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


__all__ = [
    "ProjectInsight",
    "record_project_insight",
    "list_project_insights",
    "rank_projects_by_contribution",
]
