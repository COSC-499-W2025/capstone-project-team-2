from pathlib import Path

from src.storage.dedup_index import deduplicate_project, _file_hash


def test_deduplicate_project_identifies_duplicates(tmp_path):
    """
    Detect duplicate content without deleting files.

    Args:
        tmp_path: Pytest-provided temp directory.
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
        tmp_path: Pytest-provided temp directory.
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
        tmp_path: Pytest-provided temp directory.
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
