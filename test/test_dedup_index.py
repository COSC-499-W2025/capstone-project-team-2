import json
from pathlib import Path

import pytest

import src.storage.dedup_index as dedup_mod
from src.storage.dedup_index import _file_hash, deduplicate_project


def test_deduplicate_project_identifies_duplicates(tmp_path):
    """
    Detect duplicate content across different projects without deleting files.
    Args:
        tmp_path (Path): Pytest-provided temp directory.
    Returns:
        None
    """
    # First project establishes the original file
    proj1 = tmp_path / "proj1"
    proj1.mkdir()
    f1 = proj1 / "a.txt"
    f1.write_text("hello")

    # Second project has a duplicate of the same content
    proj2 = tmp_path / "proj2"
    proj2.mkdir()
    f2 = proj2 / "b.txt"
    f2.write_text("hello")  # duplicate content

    index_path = tmp_path / "dedup_index.json"

    # Index the first project
    result1 = deduplicate_project(proj1, index_path)
    assert result1.unique_files == 1
    assert result1.duplicate_files == 0

    # Index the second project - should detect duplicate across projects
    result2 = deduplicate_project(proj2, index_path)

    assert result2.unique_files == 0
    assert result2.duplicate_files == 1
    assert len(result2.duplicates) == 1
    assert Path(result2.duplicates[0]["path"]).name == "b.txt"
    assert Path(result2.duplicates[0]["original"]).name == "a.txt"
    assert result2.removed == 0


def test_file_hash_is_stable(tmp_path):
    """
    Ensure hashing the same file twice returns the same digest.
    Args:
        tmp_path (Path): Pytest-provided temp directory.
    Returns:
        None
    """
    f = tmp_path / "file.bin"
    f.write_bytes(b"abc")

    h1 = _file_hash(f)
    h2 = _file_hash(f)

    assert h1 == h2


def test_deduplicate_project_can_remove_duplicates(tmp_path):
    """
    Delete duplicate files when removal flag is set (across different projects).
    Args:
        tmp_path (Path): Pytest-provided temp directory.
    Returns:
        None
    """
    # First project establishes the original file
    proj1 = tmp_path / "proj1"
    proj1.mkdir()
    f1 = proj1 / "a.txt"
    f1.write_text("same")

    # Second project has a duplicate
    proj2 = tmp_path / "proj2"
    proj2.mkdir()
    f2 = proj2 / "b.txt"
    f2.write_text("same")

    index_path = tmp_path / "dedup_index.json"

    # Index the first project
    deduplicate_project(proj1, index_path)

    # Index the second project with removal enabled
    result = deduplicate_project(proj2, index_path, remove_duplicates=True)

    assert result.duplicate_files == 1
    assert result.removed == 1
    # Original file should remain, duplicate should be removed
    assert f1.exists()
    assert not f2.exists()


def test_deduplicate_project_removes_deleted_file_from_cache(tmp_path):
    """
    When a duplicate file is deleted, its per-path file cache entry should be removed.
    """
    proj1 = tmp_path / "proj1"
    proj1.mkdir()
    f1 = proj1 / "a.txt"
    f1.write_text("same")

    proj2 = tmp_path / "proj2"
    proj2.mkdir()
    f2 = proj2 / "b.txt"
    f2.write_text("same")

    index_path = tmp_path / "dedup_index.json"

    deduplicate_project(proj1, index_path)
    deduplicate_project(proj2, index_path)

    cache_key = dedup_mod._path_cache_key(f2)
    index_before = json.loads(index_path.read_text(encoding="utf-8"))
    file_cache_before = index_before.get(dedup_mod.FILE_CACHE_KEY, {})
    assert cache_key in file_cache_before

    result = deduplicate_project(proj2, index_path, remove_duplicates=True)
    assert result.removed == 1
    assert not f2.exists()

    index_after = json.loads(index_path.read_text(encoding="utf-8"))
    file_cache_after = index_after.get(dedup_mod.FILE_CACHE_KEY, {})
    assert cache_key not in file_cache_after


def test_corrupted_index_logs_warning(tmp_path, caplog):
    """
    A bad JSON index should warn and recover with an empty index.
    Args:
        tmp_path (Path): Pytest-provided temp directory.
        caplog (pytest.LogCaptureFixture): Captures log output.
    Returns:
        None
    """
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "file.txt").write_text("content")

    index_path = tmp_path / "dedup_index.json"
    index_path.write_text("{ not valid json")  # corrupt contents

    with caplog.at_level("WARNING"):
        result = deduplicate_project(proj, index_path)

    assert any("Failed to load dedup index" in msg for msg in caplog.messages)
    # Still processes files even after reset
    assert result.unique_files == 1
    assert result.duplicate_files == 0


def test_lock_contention_times_out_and_warns(tmp_path, monkeypatch, caplog):
    """
    If the lock is held elsewhere, deduplication should time out quickly and warn instead of hanging.
    Args:
        tmp_path (Path): Pytest-provided temp directory.
        monkeypatch (pytest.MonkeyPatch): Patches module attributes for the test.
        caplog (pytest.LogCaptureFixture): Captures log output.
    Returns:
        None
    """
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "file.txt").write_text("content")

    index_path = tmp_path / "dedup_index.json"
    lock_path = str(index_path) + ".lock"

    # Speed up the test by shortening the lock timeout.
    monkeypatch.setattr(dedup_mod, "LOCK_TIMEOUT", 0.05)

    lock = dedup_mod.FileLock(lock_path, timeout=dedup_mod.LOCK_TIMEOUT)
    lock.acquire(timeout=0)  # hold the lock to force contention
    try:
        with caplog.at_level("WARNING"):
            result = deduplicate_project(proj, index_path)
    finally:
        lock.release()

    assert result.unique_files == 0
    assert result.duplicate_files == 0
    assert any("Could not acquire dedup index lock" in msg for msg in caplog.messages)


def test_unchanged_files_reuse_cached_hash(tmp_path, monkeypatch):
    """
    On re-analysis of unchanged files, dedup should reuse cached digest instead of re-hashing.
    """
    proj = tmp_path / "proj"
    proj.mkdir()
    f = proj / "file.txt"
    f.write_text("content")
    index_path = tmp_path / "dedup_index.json"

    calls = {"count": 0}
    original = dedup_mod._file_hash

    def counting_hash(path: Path) -> str:
        calls["count"] += 1
        return original(path)

    monkeypatch.setattr(dedup_mod, "_file_hash", counting_hash)

    deduplicate_project(proj, index_path)
    assert calls["count"] == 1

    # Same file, unchanged metadata/content -> should reuse cached hash.
    deduplicate_project(proj, index_path)
    assert calls["count"] == 1


def test_changed_files_are_rehashed(tmp_path, monkeypatch):
    """
    If a file changes, dedup should recompute its hash and refresh cache entry.
    """
    proj = tmp_path / "proj"
    proj.mkdir()
    f = proj / "file.txt"
    f.write_text("v1")
    index_path = tmp_path / "dedup_index.json"

    calls = {"count": 0}
    original = dedup_mod._file_hash

    def counting_hash(path: Path) -> str:
        calls["count"] += 1
        return original(path)

    monkeypatch.setattr(dedup_mod, "_file_hash", counting_hash)

    deduplicate_project(proj, index_path)
    assert calls["count"] == 1

    # Use different byte length so fingerprint changes even if mtime granularity is coarse.
    f.write_text("v2-updated")
    deduplicate_project(proj, index_path)
    assert calls["count"] == 2
