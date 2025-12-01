from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.saved_projects as mod


def test_list_saved_projects_filters_config_and_dedupes(tmp_path):
    new_dir = tmp_path / "project_insights"
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

    projects = mod.list_saved_projects(new_dir)
    names = {p.name for p in projects}

    assert "legacy.json" in names
    assert "new.json" in names
    assert "dup.json" in names
    assert "UserConfigs.json" not in names
    assert len(projects) == 4


def test_show_saved_summary_prints_contributors(monkeypatch, tmp_path, capsys):
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


def test_get_saved_projects_from_db_uses_cursor(monkeypatch):
    rows = [(1, "file.json", "{}", "2024-01-01")]

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
    ctx = SimpleNamespace(conn=SimpleNamespace(cursor=lambda: cursor))

    result = mod.get_saved_projects_from_db(ctx)

    assert result == rows
    assert cursor.executed is True
    assert cursor.closed is True


def test_delete_file_from_disk_respects_references(monkeypatch, tmp_path):
    ctx = SimpleNamespace(
        default_save_dir=tmp_path / "project_insights",
        store=SimpleNamespace(count_file_references=MagicMock(return_value=1)),
    )
    ctx.default_save_dir.mkdir()
    file_path = ctx.default_save_dir / "kept.json"
    file_path.write_text("{}")

    deleted = mod.delete_file_from_disk("kept.json", ctx)

    assert deleted is False
    assert file_path.exists()


def test_delete_file_from_disk_deletes_when_no_references(monkeypatch, tmp_path):
    ctx = SimpleNamespace(
        default_save_dir=tmp_path / "project_insights",
        store=SimpleNamespace(count_file_references=MagicMock(return_value=0)),
    )
    ctx.default_save_dir.mkdir()
    file_path = ctx.default_save_dir / "remove.json"
    file_path.write_text("{}")

    deleted = mod.delete_file_from_disk("remove.json", ctx)

    assert deleted is True
    assert file_path.exists() is False
