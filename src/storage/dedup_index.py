"""Simple content-hash deduplication index for project uploads.

Stores SHA-256 hashes for every file seen across uploads so later snapshots
can avoid storing duplicates. A duplicate is the same hash with a different
path; we keep the first-seen path as canonical.

The index lives alongside saved analyses (default: User_config_files/project_insights)
as `dedup_index.json`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


CHUNK_SIZE = 1024 * 1024  # 1 MB


@dataclass
class DedupResult:
    unique_files: int
    duplicate_files: int
    duplicates: List[dict]
    index_size: int
    removed: int = 0


def _file_hash(path: Path) -> str:
    """
    Return the SHA-256 hex digest of a file.

    Args:
        path (Path): File to hash.

    Returns:
        str: Hex digest string.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_index(index_path: Path) -> Dict[str, dict]:
    """
    Load the hash index from disk.

    Args:
        index_path (Path): Location of the index file.

    Returns:
        dict: Loaded index or empty dict on failure.
    """
    if index_path.exists():
        try:
            return json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_index(index_path: Path, index: Dict[str, dict]) -> None:
    """
    Persist the hash index to disk.

    Args:
        index_path (Path): Destination path.
        index (dict): Hash map to store.
    """
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")


def deduplicate_project(root: Path, index_path: Path, remove_duplicates: bool = False) -> DedupResult:
    """Scan all files under root, update index, and report duplicates.

    Args:
        root: Project root to scan.
        index_path: Location of the persistent hash index.
        remove_duplicates: When True, delete duplicate files after recording them.
    """
    index = _load_index(index_path)
    duplicates: List[dict] = []
    unique_files = 0
    removed = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            digest = _file_hash(path)
        except Exception:
            # Skip unreadable files but continue processing others
            continue

        record = index.get(digest)
        if record:
            dup_entry = {
                "path": str(path),
                "original": record.get("path"),
                "project": record.get("project"),
                "removed": False,
            }
            if remove_duplicates:
                try:
                    path.unlink(missing_ok=True)
                    dup_entry["removed"] = True
                    removed += 1
                except Exception:
                    # If delete fails, keep entry but mark as not removed
                    dup_entry["removed"] = False
            duplicates.append(dup_entry)
        else:
            index[digest] = {"path": str(path), "project": root.name}
            unique_files += 1

    _save_index(index_path, index)

    return DedupResult(
        unique_files=unique_files,
        duplicate_files=len(duplicates),
        duplicates=duplicates,
        index_size=len(index),
        removed=removed,
    )
