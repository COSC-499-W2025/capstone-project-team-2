"""
Menu flow tests for the CLI and insights menu, including helper coverage.
Exercises the primary user paths plus the shared insight helpers used by the menu flows.
"""

from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import pytest

# Smoke tests for menu dispatch flows using monkeypatched input.
import src.menus as mod
from src import insight_helpers

def _inputs(values):
    """Yield successive inputs to simulate user interaction across menu prompts."""
    it = iter(values)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return ""

    return fake_input

def test_analyze_project_menu_directory_invokes_analyze(monkeypatch):
    """Directory option routes to analyze_project with input path."""
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
    """ZIP option extracts then analyzes with ZIP stem as project label."""
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
    """Saved projects menu lists items and calls show_saved_summary."""
    item = Path("/tmp/a.json")
    monkeypatch.setattr(mod, "list_saved_projects", lambda folder: [item])
    monkeypatch.setattr(mod, "show_saved_summary", lambda path: None)
    monkeypatch.setattr("builtins.input", _inputs(["1", ""]))

    ctx = SimpleNamespace(default_save_dir=Path("/tmp/default"), external_consent=False)
    mod.saved_projects_menu(ctx)

def test_delete_analysis_menu_deletes(monkeypatch, tmp_path):
    """Delete menu removes DB record for the chosen file."""
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
    """Selecting 0 exits main menu with status code 0."""
    monkeypatch.setattr("builtins.input", _inputs(["0"]))
    result = mod.main_menu(SimpleNamespace())
    assert result == 0

def test_main_menu_routes_to_insights_menu(monkeypatch):
    """Option 7 should dispatch to project_insights_menu."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["7", "0"]))
    monkeypatch.setattr(mod, "project_insights_menu", lambda ctx: called.setdefault("hit", True))
    mod.main_menu(SimpleNamespace())
    assert called.get("hit") is True

def test_ai_resume_line_menu_no_external_consent(monkeypatch, tmp_path):
    """
    If 'consented.external' is False in UserConfigs.json,
    the AI résumé menu should NOT call list_saved_projects or GenerateProjectResume.

    Verifies:
    - Consent gating short-circuits downstream calls
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

    Verifies:
    - The chosen project_root flows into GenerateProjectResume
    - generate() is invoked with saveToJson=False
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
        """Minimal stub for GenerateProjectResume to track call parameters."""
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

def test_project_insights_menu_lists_projects(monkeypatch, tmp_path):
    """Insights menu lists projects from storage path."""
    storage = tmp_path / "project_insights.json"
    ctx = SimpleNamespace(legacy_save_dir=tmp_path)

    captured_path = {}

    def fake_list_projects(storage_path):
        captured_path["path"] = storage_path
        return [
            SimpleNamespace(
                project_name="Demo",
                analyzed_at="2024-01-01",
                project_type="individual",
                detection_mode="git",
                languages=["Python"],
                frameworks=["FastAPI"],
            )
        ]

    import src.menu_insights as mi
    monkeypatch.setattr(mi, "list_project_insights", fake_list_projects)
    monkeypatch.setattr(mi, "list_skill_history", lambda storage_path: [])
    monkeypatch.setattr(mi, "rank_projects_by_contribution", lambda **kwargs: [])
    monkeypatch.setattr(mi, "summaries_for_top_ranked_projects", lambda **kwargs: [])
    # choice=1, language="", skill="", since="", enter to continue, then exit
    monkeypatch.setattr("builtins.input", _inputs(["1", "", "", "", "", "0"]))

    mod.project_insights_menu(ctx)
    assert captured_path["path"] == storage

def test_project_insights_menu_ranks_projects(monkeypatch, tmp_path):
    """
    Insights menu should honor contributor filters and composite scoring.

    Verifies:
    - rank_projects_by_contribution is invoked when contributor is provided
    - Composite ranking prefers more recent, higher-skill items
    """
    storage = tmp_path / "project_insights.json"
    ctx = SimpleNamespace(legacy_save_dir=tmp_path)

    captured_rank = {}
    # create two insights with different dates and skills to ensure composite sorting works
    now = datetime.now(timezone.utc)
    recent = now.isoformat()
    old = (now - timedelta(days=200)).isoformat()

    insights = [
        SimpleNamespace(
            project_name="OldLow",
            stats={"contributors": 1},
            contribution_score=lambda c=None: 1,
            languages=["Python"],
            frameworks=[],
            skills=["SQL"],
            summary="Old project",
            analyzed_at=old,
        ),
        SimpleNamespace(
            project_name="NewHigh",
            stats={"contributors": 2},
            contribution_score=lambda c=None: 2,
            languages=["Java"],
            frameworks=[],
            skills=["Java", "Spring"],
            summary="New project",
            analyzed_at=recent,
        ),
    ]

    def fake_rank(storage_path, contributor=None, top_n=None):
        captured_rank["called"] = True
        return insights

    # Patch inside menu_insights module so delegation picks up the fake
    import src.menu_insights as mi
    monkeypatch.setattr(mi, "rank_projects_by_contribution", fake_rank)
    monkeypatch.setattr(mi, "list_project_insights", lambda storage_path: insights)
    monkeypatch.setattr(mi, "list_skill_history", lambda storage_path: [])
    monkeypatch.setattr(mi, "summaries_for_top_ranked_projects", lambda **kwargs: [])
    # choice=3, contributor="Alice" (forces rank_projects_by_contribution), language blank, skill blank, since blank, top_n=5, enter to continue, exit
    monkeypatch.setattr("builtins.input", _inputs(["3", "Alice", "", "", "", "5", "", "0"]))

    mod.project_insights_menu(ctx)
    assert captured_rank.get("called") is True
    # Verify composite ranking prefers newer project with more skills
    scores = [
        insight_helpers.compute_composite_score(insights[0])[0],
        insight_helpers.compute_composite_score(insights[1])[0],
    ]
    assert scores[1] > scores[0]

def test_insight_helper_filter_and_score_smoke():
    """Quick sanity checks for filter_insights and compute_composite_score helpers."""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=400)

    recent = SimpleNamespace(
        analyzed_at=now.isoformat(),
        languages=["Python"],
        skills=["ML", "Data"],
        contribution_score=lambda c=None: 1,
    )
    stale = SimpleNamespace(
        analyzed_at=old.isoformat(),
        languages=["Java"],
        skills=["DevOps"],
        contribution_score=lambda c=None: 2,
    )

    filtered = insight_helpers.filter_insights([recent, stale], language="python")
    assert filtered == [recent]

    filtered = insight_helpers.filter_insights([recent, stale], skill="devops")
    assert filtered == [stale]

    filtered = insight_helpers.filter_insights([recent, stale], since=now - timedelta(days=30))
    assert filtered == [recent]

    score_recent, _ = insight_helpers.compute_composite_score(recent)
    score_stale, _ = insight_helpers.compute_composite_score(stale)
    assert score_recent > score_stale
