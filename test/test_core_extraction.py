import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from src.core.extraction import extractInfo


@pytest.fixture
def zip_workspace(tmp_path):
    valid_zip = tmp_path / "valid.zip"
    empty_zip = tmp_path / "empty.zip"
    invalid_zip = tmp_path / "invalid.zip"

    with zipfile.ZipFile(valid_zip, "w") as zf:
        zf.writestr("file1.txt", "hello")
        zf.writestr("file2.txt", "world")

    with zipfile.ZipFile(empty_zip, "w"):
        pass

    invalid_zip.write_text("not-a-real-zip", encoding="utf-8")

    return {
        "valid_zip": valid_zip,
        "empty_zip": empty_zip,
        "invalid_zip": invalid_zip,
    }


def _cleanup_path(path_or_error: str) -> None:
    if isinstance(path_or_error, str) and not path_or_error.startswith("Error"):
        shutil.rmtree(path_or_error, ignore_errors=True)


def test_verifyzip_missing_path_returns_path_error(tmp_path):
    missing = tmp_path / "missing.zip"
    text = extractInfo().verifyZIP(missing)
    assert text is not None
    assert extractInfo.PATH_ERROR_TEXT in text


def test_verifyzip_non_zip_returns_not_zip_error(zip_workspace):
    text = extractInfo().verifyZIP(zip_workspace["invalid_zip"])
    assert text == extractInfo.NOT_ZIP_ERROR_TEXT


def test_run_extraction_valid_zip_extracts_contents(zip_workspace):
    output = extractInfo().runExtraction(zip_workspace["valid_zip"])
    try:
        out_dir = Path(output)
        assert out_dir.exists()
        assert (out_dir / "file1.txt").exists()
        assert (out_dir / "file2.txt").exists()
    finally:
        _cleanup_path(output)


def test_run_extraction_empty_zip_returns_empty_dir(zip_workspace):
    output = extractInfo().runExtraction(zip_workspace["empty_zip"])
    try:
        out_dir = Path(output)
        assert out_dir.exists()
        assert list(out_dir.iterdir()) == []
    finally:
        _cleanup_path(output)


def test_run_extraction_missing_path_returns_error(tmp_path):
    missing = tmp_path / "missing.zip"
    text = extractInfo().runExtraction(missing)
    assert text is not None
    assert extractInfo.PATH_ERROR_TEXT in text


def test_run_extraction_corrupt_internal_zip_returns_corrupt_file_error():
    path = Path(__file__).resolve().parent / "TestZIPs" / "CorruptInternalZIP.zip"
    text = extractInfo().runExtraction(path)
    assert text is not None
    assert extractInfo.CORRUPT_FILE_ERROR_TEXT in text

