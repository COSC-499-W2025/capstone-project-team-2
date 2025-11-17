from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import shutil
import logging
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.project_skill_insights import identify_skills
from src.individual_contribution_detection import detect_individual_contributions

logger = logging.getLogger(__name__)

# Cache: maps tuple of file paths → detected skills
skills_cache: Dict[Tuple[str, ...], List[str]] = {}

"""
Associates individual contributors with the specific skills they demonstrate
through their file contributions in collaborative projects.

Copies each contributor's files to a temp directory and runs
the existing skill detection on that subset.
"""

def associate_contribution_skills(project_root: Path | str) -> Dict[str, Dict]:
    
    """
    Analyze a collaborative project and determine which skills each contributor demonstrates.

    Args:
        project_root: Path to the project directory

    Returns:
        dict: {
            "project_skills": [...],
            "contributors": {
                "Alice": {"file_count": int, "skills": [...]},
                ...
            }
        }

    """
    root = Path(project_root)

    contribution_data = detect_individual_contributions(root)
    if not contribution_data.get("is_collaborative"):
        # Return empty structure for non-collaborative projects
        return {"project_skills": [], "contributors": {}}

    contributors = contribution_data.get("contributors", {})

    # Detect project-wide skills for context
    project_skills = identify_skills(root) or []
    project_skills = stable_unique_sorted(project_skills)

    result: Dict[str, Dict] = {
        "project_skills": project_skills,
        "contributors": {}
    }

    for contributor, data in contributors.items():
        files = dedupe_ordered(data.get("files_owned", []) or [])
        skills = get_skills_for_file_subset(root, files)

        result["contributors"][contributor] = {
            "file_count": len(files),
            "skills": skills
        }

    return result

def get_skills_for_file_subset(root: Path, files: List[str]) -> List[str]:
    
    """
    Detect skills shown in a contributor's subset of files.

    Copies only those files into a temporary directory and runs identify_skills().
    """
    
    if not files:
        return []
    
    cache_key = tuple(files)
    if cache_key in skills_cache:
        return skills_cache[cache_key]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)

        for file_path in files:
            src = root / file_path
            if not src.is_file():
                logger.warning("Contributor file missing or invalid: %s", src)
                continue

            dest = temp_root / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dest)
            except (OSError, PermissionError):
                logger.exception("Failed to copy file to temp directory: %s", src)
                continue

        # Run existing skill detection on the filtered project
        try:
            skills = identify_skills(temp_root) or []
        except Exception as exc:
            logger.exception("identify_skills failed for temp contribution set: %s", exc)
            skills = []

    skills = stable_unique_sorted(skills)
    skills_cache[cache_key] = skills
    return skills

def dedupe_ordered(items: List[str]) -> List[str]:
    
    """Return items with duplicates removed while preserving original order."""
    
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out

def stable_unique_sorted(items: List[str]) -> List[str]:
    
    """Return items with duplicates removed, then sorted deterministically."""

    return sorted(set(items))

def clear_skills_cache():
    
    """Clear the skills cache. Useful in long-running processes or tests."""
    
    skills_cache.clear()

__all__ = ["associate_contribution_skills", "clear_skills_cache"]

