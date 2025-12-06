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
        lambda path, ctx, use_ai_analysis=False: called.setdefault("path", path),
    )

    ctx = SimpleNamespace(
        external_consent=False
    )
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
        lambda path, ctx, project_label=None, use_ai_analysis=False: called.setdefault(
            "data", (path, project_label)
        ),
    )

    ctx = SimpleNamespace(
        external_consent=False
    )
    mod.analyze_project_menu(ctx)

    assert called["data"][0] == Path("/tmp/unzipped")
    assert called["data"][1] == "project"


def test_saved_projects_menu_shows_selected_file(monkeypatch):
    item = Path("/tmp/a.json")
    monkeypatch.setattr(mod, "list_saved_projects", lambda folder: [item])
    monkeypatch.setattr(mod, "show_saved_summary", lambda path: None)
    monkeypatch.setattr("builtins.input", _inputs(["1", ""]))

    ctx = SimpleNamespace(default_save_dir=Path("/tmp/default"), external_consent=False)
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
    monkeypatch.setattr(mod, "delete_file_from_disk", lambda filename, ctx: False)
    monkeypatch.setattr("builtins.input", _inputs(["1", "y", "n"]))

    ctx = SimpleNamespace(default_save_dir=tmp_path, external_consent=False)
    mod.delete_analysis_menu(ctx)

    assert delete_calls["id"] == 1

def test_main_menu_exit_returns_zero(monkeypatch):
    monkeypatch.setattr("builtins.input", _inputs(["0"]))
    result = mod.main_menu(SimpleNamespace())
    assert result == 0

def test_ai_resume_line_menu_no_external_consent(monkeypatch, tmp_path):
    """
    If 'consented.external' is False in UserConfigs.json,
    the AI résumé menu should NOT call list_saved_projects or GenerateProjectResume.
    """
    # Create a fake UserConfigs.json with external consent = False
    config_path = tmp_path / "UserConfigs.json"
    config_path.write_text(
        '{"consented": {"external": false, "Data consent": true}}',
        encoding="utf-8",
    )

    # Track calls
    called = {"list_saved": False, "gpr": False}

    monkeypatch.setattr(
        mod,
        "list_saved_projects",
        lambda folder: called.__setitem__("list_saved", True),
    )
    monkeypatch.setattr(
        mod,
        "GenerateProjectResume",
        lambda project_root: called.__setitem__("gpr", True),
    )

    # ctx only needs legacy/default dirs for this test
    ctx = SimpleNamespace(
        default_save_dir=tmp_path,
        legacy_save_dir=tmp_path,
    )

    # Run the menu (should return early)
    mod.ai_resume_line_menu(ctx)

    # Because external consent is False, nothing downstream should be called
    assert called["list_saved"] is False
    assert called["gpr"] is False

def test_ai_resume_line_menu_with_external_consent_and_selection(monkeypatch, tmp_path):
    """
    When external consent is True and the user selects a saved project,
    the menu should call GenerateProjectResume(project_root).generate(saveToJson=False).
    """
    import json

    # Config with external consent = True
    config_path = tmp_path / "UserConfigs.json"
    config_path.write_text(
        '{"consented": {"external": true, "Data consent": true}}',
        encoding="utf-8",
    )

    # Fake saved analysis JSON containing project_root
    analysis_path = tmp_path / "my_project_analysis.json"
    project_root = str(tmp_path / "my_project")
    analysis_path.write_text(
        json.dumps({"project_root": project_root}),
        encoding="utf-8",
    )

    # list_saved_projects should return exactly this file
    monkeypatch.setattr(
        mod,
        "list_saved_projects",
        lambda folder: [analysis_path],
    )

    # Simulate user selecting "1" then Enter to continue
    monkeypatch.setattr("builtins.input", _inputs(["1", ""]))

    # Mock GenerateProjectResume and track calls
    calls = {"project_root": None, "saveToJson": None}

    class FakeGPR:
        def __init__(self, root):
            calls["project_root"] = root

        def generate(self, saveToJson: bool):
            calls["saveToJson"] = saveToJson
            # return a minimal fake ResumeItem-like object
            return SimpleNamespace(
                project_title="My Project",
                one_sentence_summary="Built a cool thing.",
                tech_stack="Python; frameworks Flask",
                impact="Improved dev workflow.",
            )

    monkeypatch.setattr(mod, "GenerateProjectResume", FakeGPR)

    ctx = SimpleNamespace(
        default_save_dir=tmp_path,
        legacy_save_dir=tmp_path,
    )

    mod.ai_resume_line_menu(ctx)

    # Assert we passed the correct project_root into GenerateProjectResume
    assert calls["project_root"] == project_root
    # And that generate() was called with saveToJson=False
    assert calls["saveToJson"] is False
