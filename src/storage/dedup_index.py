"""Simple content-hash deduplication index for project uploads.

Stores SHA-256 hashes for every file seen across uploads so later snapshots
can avoid storing duplicates. A duplicate is the same hash with a different
path; we keep the first-seen path as canonical.

The index lives alongside saved analyses (default: User_config_files/project_insights)
as `dedup_index.json`.
"""

from __future__ import annotations

import logging
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from filelock import FileLock, Timeout


CHUNK_SIZE = 1024 * 1024  # 1 MB
LOCK_TIMEOUT = 10  # seconds
FILE_CACHE_KEY = "__file_cache__"


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


def _load_index(index_path: Path) -> Tuple[Dict[str, dict], Dict[str, dict]]:
    """
    Load the hash index from disk.

    Args:
        index_path (Path): Location of the index file.

    Returns:
        Tuple[Dict[str, dict], Dict[str, dict]]:
            Hash index plus per-path metadata cache.
    """
    if index_path.exists():
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {}, {}

            file_cache = raw.get(FILE_CACHE_KEY, {})
            if not isinstance(file_cache, dict):
                file_cache = {}

            hash_index: Dict[str, dict] = {
                k: v for k, v in raw.items() if k != FILE_CACHE_KEY and isinstance(v, dict)
            }
            return hash_index, file_cache
        except Exception as e:
            logging.warning("Failed to load dedup index at %s: %s", index_path, e)
            return {}, {}
    return {}, {}


def _save_index(index_path: Path, index: Dict[str, dict], file_cache: Dict[str, dict]) -> None:
    """
    Persist the hash index to disk.

    Args:
        index_path (Path): Destination path.
        index (dict): Hash map to store.
        file_cache (dict): Path metadata cache used to skip unnecessary re-hashing.
    """
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(index)
    payload[FILE_CACHE_KEY] = file_cache
    index_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _path_cache_key(path: Path) -> str:
    """Return a stable cache key for path-based metadata."""
    return str(path.resolve())


def _stat_fingerprint(path: Path) -> Tuple[int, int, int]:
    """Return lightweight file metadata used to detect unchanged files."""
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _digest_for_path(path: Path, file_cache: Dict[str, dict]) -> str:
    """
    Return content digest for a file, reusing cached hash when metadata is unchanged.

    The cache uses file size + nanosecond mtime/ctime as a cheap pre-check.
    """
    cache_key = _path_cache_key(path)
    size, mtime_ns, ctime_ns = _stat_fingerprint(path)
    cached = file_cache.get(cache_key)

    if (
        isinstance(cached, dict)
        and cached.get("size") == size
        and cached.get("mtime_ns") == mtime_ns
        and cached.get("ctime_ns") == ctime_ns
        and isinstance(cached.get("hash"), str)
    ):
        return cached["hash"]

    digest = _file_hash(path)
    file_cache[cache_key] = {
        "size": size,
        "mtime_ns": mtime_ns,
        "ctime_ns": ctime_ns,
        "hash": digest,
    }
    return digest


def deduplicate_project(root: Path, index_path: Path, remove_duplicates: bool = False) -> DedupResult:
    """Scan all files under root, update index, and report duplicates.

    Args:
        root: Project root to scan.
        index_path: Location of the persistent hash index.
        remove_duplicates: When True, delete duplicate files after recording them.
    """
    lock_path = str(index_path) + ".lock"
    lock = FileLock(lock_path, timeout=LOCK_TIMEOUT)

    try:
        with lock:
            index, file_cache = _load_index(index_path)
            duplicates: List[dict] = []
            unique_files = 0
            removed = 0

            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    digest = _digest_for_path(path, file_cache)
                except Exception:
                    # Skip unreadable files but continue processing others
                    continue

                record = index.get(digest)
                if record:
                    # Skip if duplicate is from the same project (re-analysis)
                    if record.get("project") == root.name:
                        # Update the index entry with current path and count as unique
                        index[digest] = {"path": str(path), "project": root.name}
                        unique_files += 1
                        continue

                    dup_entry = {
                        "path": str(path),
                        "original": record.get("path"),
                        "project": record.get("project"),
                        "removed": False,
                    }
                    if remove_duplicates:
                        try:
                            path.unlink(missing_ok=True)
                            file_cache.pop(_path_cache_key(path), None)
                            dup_entry["removed"] = True
                            removed += 1
                        except Exception:
                            # If delete fails, keep entry but mark as not removed
                            dup_entry["removed"] = False
                    duplicates.append(dup_entry)
                else:
                    index[digest] = {"path": str(path), "project": root.name}
                    unique_files += 1

            _save_index(index_path, index, file_cache)

            return DedupResult(
                unique_files=unique_files,
                duplicate_files=len(duplicates),
                duplicates=duplicates,
                index_size=len(index),
                removed=removed,
            )
    except Timeout:
        logging.warning(
            "Could not acquire dedup index lock at %s within %ss; skipping deduplication for %s",
            lock_path,
            LOCK_TIMEOUT,
            root,
        )
        return DedupResult(unique_files=0, duplicate_files=0, duplicates=[], index_size=0, removed=0)
