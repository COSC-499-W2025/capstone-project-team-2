"""
resume_exporter
===============

Utilities to discover project directories, generate ResumeItem objects, and
export them to a JSON file. Also provides a CLI entry point for quick usage.

Key functions:
- discover_projects(root): enumerate first-level project directories
- build_resume_items(root): generate ResumeItem for each project directory
- export_resume_items(root, destination): write JSON file with all projects
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .resume_item_generator import ResumeItem, generate_resume_item


def discover_projects(root: Path | str) -> List[Path]:
    """
    Return a stable list of project directories contained within ``root``.

    Hidden directories and files are ignored; only first-level directories are considered
    to keep the output predictable for résumé generation.

    Args:
        root: Path to a folder containing project subdirectories.

    Returns:
        Sorted list of first-level, non-hidden directories.
    """
    root_path = Path(root)
    if not root_path.exists():
        return []

    projects: List[Path] = []
    # We sort child entries so the output order is deterministic.
    for child in sorted(root_path.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            projects.append(child)
    return projects


def build_resume_items(root: Path | str) -> List[ResumeItem]:
    """
    Generate ``ResumeItem`` objects for each project directory beneath ``root``.

    Args:
        root: Path to a folder with project subdirectories.

    Returns:
        List of ResumeItem instances, one per project directory discovered.
    """
    items: List[ResumeItem] = []
    for project_dir in discover_projects(root):
        items.append(generate_resume_item(project_dir))
    return items


def export_resume_items(
    root: Path | str,
    destination: Optional[Path | str] = None,
) -> Path:
    """
    Build résumé items for sub-projects in ``root`` and persist them to JSON.

    Args:
        root: Directory that contains one or more project folders.
        destination: Where the JSON should be written. Defaults to
            ``root / "resume_items.json"``.

    Returns:
        Path to the written JSON file.
    """
    root_path = Path(root).resolve()

    #new validation block
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f"Invalid root path: {root_path}. Must be an existing directory.")
    
    if destination is None:
        destination_path = root_path / "resume_items.json"
    else:
        destination_path = Path(destination).resolve()

    resume_items = build_resume_items(root_path)

    # Minimal, stable payload that can be extended in the future.
    payload: Dict[str, object] = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "root": str(root_path),
        "projects": [asdict(item) for item in resume_items],
    }

    destination_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination_path


def _cli(argv: Optional[Iterable[str]] = None) -> int:
    """
    CLI entry point.
    Usage:
        python -m src.resume_exporter <root> [-o OUTPUT]
    """
    parser = argparse.ArgumentParser(
        description="Generate résumé-ready items for each project in a directory.",
    )
    parser.add_argument(
        "root",
        help="Path to the directory containing project folders.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="Destination JSON file (defaults to <root>/resume_items.json).",
    )

    args = parser.parse_args(argv)
    export_resume_items(args.root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
