from pathlib import Path

import pytest

import src.storage.dedup_index as dedup_mod
from src.storage.dedup_index import _file_hash, deduplicate_project


def test_deduplicate_project_identifies_duplicates(tmp_path):
    """
    Detect duplicate content without deleting files.
    Args:
        tmp_path (Path): Pytest-provided temp directory.
    Returns:
        None
    """
    proj = tmp_path / "proj"
    proj.mkdir()

    f1 = proj / "a.txt"
    f2 = proj / "b.txt"
    f1.write_text("hello")
    f2.write_text("hello")  # duplicate content

    index_path = tmp_path / "dedup_index.json"

    result = deduplicate_project(proj, index_path)

    assert result.unique_files == 1
    assert result.duplicate_files == 1
    assert len(result.duplicates) == 1
    dup_paths = {Path(result.duplicates[0]["path"]).name, Path(result.duplicates[0]["original"]).name}
    assert dup_paths == {"a.txt", "b.txt"}
    assert result.removed == 0


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
    Delete duplicate files when removal flag is set.
    Args:
        tmp_path (Path): Pytest-provided temp directory.
    Returns:
        None
    """
    proj = tmp_path / "proj"
    proj.mkdir()

    f1 = proj / "a.txt"
    f2 = proj / "b.txt"
    f1.write_text("same")
    f2.write_text("same")

    index_path = tmp_path / "dedup_index.json"

    result = deduplicate_project(proj, index_path, remove_duplicates=True)

    assert result.duplicate_files == 1
    assert result.removed == 1
    # Exactly one of the two files should remain after removal.
    remaining = sum(p.exists() for p in (f1, f2))
    assert remaining == 1


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
