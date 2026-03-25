"""
User-controlled presentation preferences for insights and showcases:
This module lets users override how project information is represented by
storing preferences such as custom project ordering, chronology fixes,
comparison attributes, highlighted skills, and showcase selections.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.reporting import project_insights
from src.reporting.project_insights import ProjectInsight, list_project_insights

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREFERENCES_PATH = _PROJECT_ROOT / "User_config_files" / "representation_preferences.json"

DEFAULT_PREFERENCES: Dict[str, Any] = {
    "project_order": [],
    "chronology_corrections": {},
    "comparison_attributes": ["languages", "frameworks", "duration_estimate"],
    "highlight_skills": [],
    "showcase_projects": [],
    "project_overrides": {},
}

def _ensure_parent(path: Path) -> None:
    """
    Ensure parent directory exists.

    Args: path: Target file path whose parent should exist.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

def load_preferences(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load representation preferences, falling back to defaults on error.

    Args: path: Optional override path to the preferences file.

    Returns:  Dict[str, Any]: Merged preferences with defaults filled in.
    """

    target = path or PREFERENCES_PATH

    if not target.exists():
        return dict(DEFAULT_PREFERENCES)

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(DEFAULT_PREFERENCES)
        merged = dict(DEFAULT_PREFERENCES)
        for key, value in data.items():
            if value is not None:
                merged[key] = value
        return merged
    except json.JSONDecodeError:
        return dict(DEFAULT_PREFERENCES)

def save_preferences(prefs: Dict[str, Any], path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Persist preferences to disk.

    Args:prefs: Preferences to write.
         path: Optional override path for writing.

    Returns: Dict[str, Any]: The same preferences that were written.
    """

    target = path or PREFERENCES_PATH
    _ensure_parent(target)
    target.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
    return prefs

def update_preferences(updates: Dict[str, Any], path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Merge updates into stored preferences and save the result.

    Args:updates: Partial preference fields to merge.
         path: Optional override path for reading/writing.

    Returns: Dict[str, Any]: The persisted, merged preferences.
    """

    target = path or PREFERENCES_PATH
    current = load_preferences(target)
    for key, value in updates.items():
        if value is not None:
            current[key] = value
    return save_preferences(current, target)


def _apply_chronology(insight: ProjectInsight, corrections: Dict[str, Any]) -> ProjectInsight:
    """
    Apply a chronology correction to an insight if provided.

    Args:insight: Original project insight.
         corrections: Mapping of project name to corrected analyzed_at.

    Returns: ProjectInsight: Possibly corrected copy of the insight.
    """

    if not corrections:
        return insight

    fix = corrections.get(insight.project_name)
    if not isinstance(fix, dict):
        return insight

    analyzed_at = fix.get("analyzed_at") or insight.analyzed_at
    return replace(insight, analyzed_at=analyzed_at)

def apply_preferences(
    insights: Optional[List[ProjectInsight]] = None,
    prefs: Optional[Dict[str, Any]] = None,
    only_showcase: bool = False,
    storage_path: Optional[Path] = None,
    pref_path: Optional[Path] = None,
    snapshot_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply stored preferences to project insights for presentation.

    Args:insights: Pre-fetched insights; if None, they are loaded from storage.
         prefs: Preference overrides; if None, preferences are loaded from disk.
         only_showcase: When True, include only showcase projects if any exist.
         storage_path: Optional custom path to the insights JSON.
         pref_path: Optional custom path to the preferences JSON.

    Returns: Dict[str, Any]: Ordered projects and the preference metadata applied.
    """

    prefs = prefs or load_preferences(pref_path)
    insights = insights or list_project_insights(
        storage_path=storage_path or project_insights.DEFAULT_STORAGE
    )

    if snapshot_label:
        insights = [i for i in insights if getattr(i, "snapshot_label", None) == snapshot_label]

    chronology = prefs.get("chronology_corrections") or {}
    corrected = [_apply_chronology(item, chronology) for item in insights]

    order_list = prefs.get("project_order") or []
    order_index = {name: idx for idx, name in enumerate(order_list)}
    ordered = sorted(
        corrected,
        key=lambda ins: (order_index.get(ins.project_name, len(order_list)), ins.analyzed_at),
    )

    showcase_set = set(prefs.get("showcase_projects") or [])
    if only_showcase and showcase_set:
        ordered = [ins for ins in ordered if ins.project_name in showcase_set]
    elif showcase_set:
        showcased: List[ProjectInsight] = []
        others: List[ProjectInsight] = []
        for ins in ordered:
            if ins.project_name in showcase_set:
                showcased.append(ins)
            else:
                others.append(ins)
        ordered = showcased + others

    project_overrides = prefs.get("project_overrides") or {}
    hydrated_projects: List[Dict[str, Any]] = []
    for insight in ordered:
        entry = insight.to_dict()
        overrides = project_overrides.get(insight.project_name, {})
        if isinstance(overrides, dict):
            override_type = str(overrides.get("contribution_type", "") or "").strip()
            override_duration = str(overrides.get("duration_estimate", "") or "").strip()
            if override_type:
                entry["project_type"] = override_type
                entry["contribution_type"] = override_type
            else:
                entry["contribution_type"] = entry.get("project_type", "unknown")
            if override_duration:
                entry["duration_estimate"] = override_duration
        else:
            entry["contribution_type"] = entry.get("project_type", "unknown")
        hydrated_projects.append(entry)

    response = {
        "projects": hydrated_projects,
        "project_order": order_list,
        "chronology_corrections": chronology,
        "comparison_attributes": prefs.get("comparison_attributes", []),
        "highlight_skills": prefs.get("highlight_skills", []),
        "showcase_projects": list(showcase_set),
        "project_overrides": project_overrides,
    }

    return response
