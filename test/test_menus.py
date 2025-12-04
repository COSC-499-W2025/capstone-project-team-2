from pathlib import Path
from types import SimpleNamespace

import pytest

# Smoke tests for menu dispatch flows using monkeypatched input.
import src.menus as mod


def _inputs(values):
    it = iter(values)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return ""

    return fake_input


def test_analyze_project_menu_directory_invokes_analyze(monkeypatch):
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["1"]))
    monkeypatch.setattr(mod, "input_path", lambda prompt, allow_blank=False: Path("/tmp/project"))
    monkeypatch.setattr(
        mod,
        "analyze_project",
        lambda path, ctx: called.setdefault("path", path),
    )

    ctx = SimpleNamespace()
    mod.analyze_project_menu(ctx)

    assert called["path"] == Path("/tmp/project")


def test_analyze_project_menu_zip_invokes_extract_and_analyze(monkeypatch):
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["2"]))
    monkeypatch.setattr(mod, "input_path", lambda prompt, allow_blank=False: Path("/tmp/project.zip"))
    monkeypatch.setattr(mod, "extract_if_zip", lambda p: Path("/tmp/unzipped"))
    monkeypatch.setattr(
        mod,
        "analyze_project",
        lambda path, ctx, project_label=None: called.setdefault(
            "data", (path, project_label)
        ),
    )

    ctx = SimpleNamespace()
    mod.analyze_project_menu(ctx)

    assert called["data"][0] == Path("/tmp/unzipped")
    assert called["data"][1] == "project"


def test_saved_projects_menu_shows_selected_file(monkeypatch):
    item = Path("/tmp/a.json")
    monkeypatch.setattr(mod, "list_saved_projects", lambda folder: [item])
    monkeypatch.setattr(mod, "show_saved_summary", lambda path: None)
    monkeypatch.setattr("builtins.input", _inputs(["1", ""]))

    ctx = SimpleNamespace(default_save_dir=Path("/tmp/default"))
    mod.saved_projects_menu(ctx)


def test_delete_analysis_menu_deletes(monkeypatch, tmp_path):
    file_path = tmp_path / "demo.json"
    file_path.write_text("{}")

    monkeypatch.setattr(mod, "list_saved_projects", lambda folder: [file_path])
    monkeypatch.setattr(
        mod,
        "get_saved_projects_from_db",
        lambda ctx: [(1, file_path.name, "2024-01-01")],
    )
    delete_calls = {}
    monkeypatch.setattr(mod, "delete_from_database_by_id", lambda record_id, ctx: delete_calls.setdefault("id", record_id))
    monkeypatch.setattr(mod, "delete_file_from_disk", lambda filename, ctx: True)
    monkeypatch.setattr("builtins.input", _inputs(["1", "y", "n"]))

    ctx = SimpleNamespace(default_save_dir=tmp_path)
    mod.delete_analysis_menu(ctx)

    assert delete_calls["id"] == 1


def test_main_menu_exit_returns_zero(monkeypatch):
    monkeypatch.setattr("builtins.input", _inputs(["0"]))
    result = mod.main_menu(SimpleNamespace())
    assert result == 0
