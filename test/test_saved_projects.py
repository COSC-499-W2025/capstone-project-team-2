from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import shutil

import pytest

# Tests for listing, summarizing, and safely deleting saved analysis artifacts.
import src.storage.saved_projects as mod
from src.core.app_context import runtimeAppContext

def test_list_saved_projects_filters_config_and_dedupes(tmp_path):
    """Check that config files are ignored and duplicates removed.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        None: Assertions validate filtering and deduplication.
    """
    new_dir = tmp_path / "project_insights"
    shutil.rmtree(new_dir)
    new_dir.mkdir()
    legacy_file = tmp_path / "legacy.json"
    new_file = new_dir / "new.json"
    dup_file = new_dir / "dup.json"

    legacy_file.write_text("{}")
    new_file.write_text("{}")
    dup_file.write_text("{}")
    # Duplicate in legacy path
    (tmp_path / "dup.json").write_text("{}")
    # Config file should be filtered
    (new_dir / "UserConfigs.json").write_text("{}")
    (new_dir / "project_insights.json").write_text("{}")
    (new_dir / "dedup_index.json").write_text("{}")
    (legacy_file.parent / "representation_preferences.json").write_text("{}")

    projects = mod.list_saved_projects(new_dir)
    names = {p.name for p in projects}

    assert "legacy.json" in names
    assert "new.json" in names
    assert "dup.json" in names
    assert "UserConfigs.json" not in names
    assert "project_insights.json" not in names
    assert "dedup_index.json" not in names
    assert "representation_preferences.json" not in names
    assert len(projects) == 4


def test_delete_file_from_disk_blocks_internal_artifacts(tmp_path):
    """
    Internal system JSON artifacts should not be deleted through this helper.
    """
    runtimeAppContext.default_save_dir = tmp_path / "project_insights"
    runtimeAppContext.default_save_dir.mkdir(parents=True, exist_ok=True)
    protected = runtimeAppContext.default_save_dir / "dedup_index.json"
    protected.write_text("{}")

    deleted = mod.delete_file_from_disk("dedup_index.json")

    assert deleted is False
    assert protected.exists() is True


def test_show_saved_summary_prints_contributors(monkeypatch, tmp_path, capsys):
    """Check that contributor summaries are printed.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.
        tmp_path: Pytest fixture providing a temporary directory.
        capsys: Pytest fixture for capturing stdout/stderr.

    Returns:
        None: Assertions validate printed summary content.
    """
    file_path = tmp_path / "analysis.json"
    data = {
        "analysis": {
            "project_root": "/tmp/demo",
            "resume_item": {
                "project_type": "collaborative",
                "detection_mode": "git",
                "languages": ["Python"],
                "frameworks": [],
                "skills": ["Python"],
                "summary": "Built demo.",
            },
            "duration_estimate": "2 days",
            "contribution_summary": {
                "metric": "files",
                "contributors": {
                    "Alice": {"file_count": 3, "percentage": "60%"},
                    "Bob": {"file_count": 2, "percentage": "40%"},
                },
            },
        }
    }
    file_path.write_text(mod.json.dumps(data))

    mod.show_saved_summary(file_path)
    out = capsys.readouterr().out

    assert "Alice" in out and "3 files" in out
    assert "Bob" in out and "2 files" in out
    assert "Résumé line" in out

def test_show_saved_summary_unclassified_doc_type_message(tmp_path, capsys):
    """Check that unknown document typing is explained clearly to users."""
    file_path = tmp_path / "analysis.json"
    data = {
        "analysis": {
            "project_root": "/tmp/demo",
            "resume_item": {
                "project_type": "individual",
                "detection_mode": "local",
                "languages": [],
                "frameworks": [],
                "skills": [],
                "summary": "Built demo.",
            },
            "document_analysis": {
                "summary": {
                    "unique_documents": 1,
                    "duplicate_documents": 0,
                    "total_words": 8,
                    "by_format": {"TXT": 1},
                    "by_type": {"unknown": 1},
                },
                "documents": [
                    {
                        "path": "scores.txt",
                        "format": "TXT",
                        "word_count": 8,
                        "doc_type": {
                            "label": "unknown",
                            "confidence": "unknown",
                            "signals": [],
                        },
                        "summary": "COSC 121 Top Students Ricardo 100 Julie 98",
                    }
                ],
                "duplicates": [],
                "errors": [],
            },
        }
    }
    file_path.write_text(mod.json.dumps(data))

    mod.show_saved_summary(file_path)
    out = capsys.readouterr().out

    assert "unclassified" in out
    assert "not enough recognizable signals" in out
    assert "No strong text patterns were detected for document typing." in out

def test_show_saved_summary_confidence_unavailable_when_label_exists(tmp_path, capsys):
    """Check fallback confidence text when type exists but confidence is missing."""
    file_path = tmp_path / "analysis.json"
    data = {
        "analysis": {
            "project_root": "/tmp/demo",
            "resume_item": {
                "project_type": "individual",
                "detection_mode": "local",
                "languages": [],
                "frameworks": [],
                "skills": [],
                "summary": "Built demo.",
            },
            "document_analysis": {
                "summary": {
                    "unique_documents": 1,
                    "duplicate_documents": 0,
                    "total_words": 42,
                    "by_format": {"MD": 1},
                    "by_type": {"report": 1},
                },
                "documents": [
                    {
                        "path": "report.md",
                        "format": "MD",
                        "word_count": 42,
                        "doc_type": {
                            "label": "report",
                            "confidence": "unknown",
                            "signals": ["report"],
                        },
                        "summary": "Quarterly report summary.",
                    }
                ],
                "duplicates": [],
                "errors": [],
            },
        }
    }
    file_path.write_text(mod.json.dumps(data))

    mod.show_saved_summary(file_path)
    out = capsys.readouterr().out

    assert "report, confidence unavailable" in out
    assert "No strong text patterns were detected for document typing." not in out

def test_get_saved_projects_from_db_uses_cursor(monkeypatch):
    """Check that the DB cursor is used and closed.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate cursor usage.
    """
    rows = [(1, "file.json", "2024-01-01")]

    class FakeCursor:
        def __init__(self):
            self.closed = False
            self.executed = False

        def execute(self, query):
            self.executed = True

        def fetchall(self):
            return rows

        def close(self):
            self.closed = True

    cursor = FakeCursor()
    monkeypatch.setattr(runtimeAppContext, "conn", SimpleNamespace(cursor=lambda: cursor))

    result = mod.get_saved_projects_from_db()

    assert result == rows
    assert cursor.executed is True
    assert cursor.closed is True

def test_delete_file_from_disk_respects_references(monkeypatch, tmp_path):
    """Check that referenced files are not deleted.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        None: Assertions validate safe delete behavior.
    """
    runtimeAppContext.default_save_dir=tmp_path / "project_insights"
    runtimeAppContext.default_save_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        runtimeAppContext,
        "store",
        SimpleNamespace(count_file_references=lambda _filename: 1),
    )
    file_path = runtimeAppContext.default_save_dir / "kept.json"
    file_path.write_text("{}")

    deleted = mod.delete_file_from_disk("kept.json")

    assert deleted is False
    assert file_path.exists()

def test_delete_file_from_disk_deletes_when_no_references(monkeypatch, tmp_path):
    """Check that unreferenced files are deleted.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        None: Assertions validate deletion behavior.
    """
    runtimeAppContext.default_save_dir=tmp_path / "project_insights"
    runtimeAppContext.default_save_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        runtimeAppContext,
        "store",
        SimpleNamespace(count_file_references=lambda _filename: 0),
    )
    file_path = runtimeAppContext.default_save_dir / "remove.json"
    file_path.write_text("{}")

    deleted = mod.delete_file_from_disk("remove.json")

    assert deleted is True
    assert file_path.exists() is False
