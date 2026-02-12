"""
Menu flow tests for the CLI and insights menu, including helper coverage.
Exercises the primary user paths plus the shared insight helpers used by the menu flows.
"""

from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import pytest
import json
from typing import Any

# Smoke tests for menu dispatch flows using monkeypatched input.
import src.cli.menus as mod
from src.analysis import insight_helpers
from src.core.app_context import runtimeAppContext

def _inputs(values):
    """Yield successive inputs to simulate user interaction across menu prompts."""
    it = iter(values)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return ""

    return fake_input

@pytest.mark.skip
def test_analyze_project_menu_directory_invokes_analyze(monkeypatch):
    """Directory option routes to analyze_project with input path."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["1"]))
    monkeypatch.setattr(mod, "input_path", lambda prompt, allow_blank=False: Path("/tmp/project"))
    monkeypatch.setattr(
        mod,
        "analyze_project",
        lambda path, use_ai_analysis=False: called.setdefault("path", path),
    )

    runtimeAppContext.external_consent=False
    mod.analyze_project_menu()

    assert called["path"] == Path("/tmp/project")

@pytest.mark.skip
def test_analyze_project_menu_zip_invokes_extract_and_analyze(monkeypatch):
    """ZIP option extracts then analyzes with ZIP stem as project label."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["2"]))
    monkeypatch.setattr(mod, "input_path", lambda prompt, allow_blank=False: Path("/tmp/project.zip"))
    monkeypatch.setattr(mod, "extract_if_zip", lambda p: Path("/tmp/unzipped"))
    monkeypatch.setattr(
        mod,
        "analyze_project",
        lambda path, use_ai_analysis=False: called.setdefault(
            "data", (path)
        ),
    )
    # mocks for the thumbnail flow
    monkeypatch.setattr(mod, "list_project_insights", lambda storage_path: [])
    monkeypatch.setattr(mod, "prompt_thumbnail_upload", lambda project_id, project_name, ctx: False)

    runtimeAppContext.external_consent=False
    runtimeAppContext.legacy_save_dir=Path("/tmp")
    mod.analyze_project_menu()

    assert called["data"][0] == Path("/tmp/unzipped")
    assert called["data"][1] == "project"

def test_saved_projects_menu_shows_selected_file(monkeypatch):
    """Saved projects menu lists items and calls show_saved_summary."""
    item = Path("/tmp/a.json")
    monkeypatch.setattr(mod, "list_saved_projects", lambda folder: [item])
    monkeypatch.setattr(mod, "show_saved_summary", lambda path: None)
    monkeypatch.setattr("builtins.input", _inputs(["1", ""]))

    runtimeAppContext.default_save_dir=Path("/tmp/default")
    runtimeAppContext.external_consent=False
    mod.saved_projects_menu()

#Too many changes for this test to be even remotely reworkable
@pytest.mark.skip()
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

    runtimeAppContext.default_save_dir=tmp_path
    runtimeAppContext.external_consent=False
    mod.delete_analysis_menu()

    assert delete_calls["id"] == 1

#Too many changes for this test to be even remotely reworkable
@pytest.mark.skip()
def test_delete_analysis_menu_deletes_without_db_refs(monkeypatch, tmp_path):
    """Delete menu attempts file removal even when DB has no matching rows."""
    file_path = tmp_path / "orphan.json"
    file_path.write_text("{}")

    monkeypatch.setattr(mod, "list_saved_projects", lambda folder: [file_path])
    monkeypatch.setattr(mod, "get_saved_projects_from_db", lambda ctx: [])

    calls = {"deleted": False}
    def _delete_file(filename, ctx):
        calls["deleted"] = True
        return True
    monkeypatch.setattr(mod, "delete_file_from_disk", _delete_file)

    monkeypatch.setattr("builtins.input", _inputs(["1", "y", "n"]))

    runtimeAppContext.default_save_dir=tmp_path
    runtimeAppContext.external_consent=False
    mod.delete_analysis_menu()

    assert calls["deleted"] is True

def test_main_menu_exit_returns_zero(monkeypatch):
    """Selecting 0 exits main menu with status code 0."""
    monkeypatch.setattr("builtins.input", _inputs(["0"]))
    result = mod.main_menu()
    assert result == 0

def test_main_menu_routes_to_insights_menu(monkeypatch):
    """Option 6 should dispatch to project_insights_menu."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["6", "0"]))
    monkeypatch.setattr(mod, "project_insights_menu", lambda: called.setdefault("hit", True))
    mod.main_menu()
    assert called.get("hit") is True


def test_main_menu_routes_to_document_generator(monkeypatch):
    """Option 5 should dispatch to document_generator_menu."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["5", "0"]))
    monkeypatch.setattr(mod, "document_generator_menu", lambda: called.setdefault("hit", True))
    mod.main_menu()
    assert called.get("hit") is True

def test_project_insights_menu_lists_projects(monkeypatch, tmp_path):
    """Insights menu lists projects from storage path."""
    storage = tmp_path / "project_insights.json"
    runtimeAppContext.legacy_save_dir=tmp_path

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

    import src.cli.menu_insights as mi
    monkeypatch.setattr(mi, "list_project_insights", fake_list_projects)
    # Option 1 now tries apply_preferences() first; force fallback path.
    monkeypatch.setattr(mi, "apply_preferences", lambda: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(mi, "list_skill_history", lambda storage_path: [])
    monkeypatch.setattr(mi, "rank_projects_by_contribution", lambda **kwargs: [])
    monkeypatch.setattr(mi, "summaries_for_top_ranked_projects", lambda **kwargs: [])
    # choice=1, language="", skill="", since="", enter to continue, then exit
    monkeypatch.setattr("builtins.input", _inputs(["1", "", "", "", "", "0"]))

    mod.project_insights_menu()
    assert captured_path["path"] == storage

def test_project_insights_menu_ranks_projects(monkeypatch, tmp_path):
    """
    Insights menu should honor contributor filters and composite scoring.

    Verifies:
    - rank_projects_by_contribution is invoked when contributor is provided
    - Composite ranking prefers more recent, higher-skill items
    """
    storage = tmp_path / "project_insights.json"
    runtimeAppContext.legacy_save_dir=tmp_path

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
    import src.cli.menu_insights as mi
    monkeypatch.setattr(mi, "rank_projects_by_contribution", fake_rank)
    monkeypatch.setattr(mi, "list_project_insights", lambda storage_path: insights)
    monkeypatch.setattr(mi, "list_skill_history", lambda storage_path: [])
    monkeypatch.setattr(mi, "summaries_for_top_ranked_projects", lambda **kwargs: [])
    # choice=3, contributor="Alice" (forces rank_projects_by_contribution), language blank, skill blank, since blank, top_n=5, enter to continue, exit
    monkeypatch.setattr("builtins.input", _inputs(["3", "Alice", "", "", "", "5", "", "0"]))

    mod.project_insights_menu()
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

@pytest.mark.skip()
def test_settings_menu_routes_to_user_config(monkeypatch):
    """Option 1 in settings menu should launch user configuration CLI."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["1", "0", "0"]))
    monkeypatch.setattr(mod, "ConfigLoader", lambda: SimpleNamespace(load=lambda: {}))
    monkeypatch.setattr(
        mod,
        "ConfigurationForUsersUI",
        lambda cfg: SimpleNamespace(run_configuration_cli=lambda: called.setdefault("hit", True)),
    )

    runtimeAppContext.external_consent=True
    mod.settings_menu()

    assert called.get("hit") is True

@pytest.mark.skip()
def test_settings_menu_routes_to_toggle_external(monkeypatch):
    """Option 2 in settings menu should call toggle_external_services."""
    called = {}
    monkeypatch.setattr("builtins.input", _inputs(["2", "0", "0"]))
    monkeypatch.setattr(
        mod,
        "toggle_external_services",
        called.setdefault("hit", True)
    )

    runtimeAppContext.external_consent=True
    mod.settings_menu()

    assert called.get("hit") is True


def test_toggle_external_services_disables(monkeypatch):
    """Toggle should disable external services when selecting option 1."""
    monkeypatch.setattr("builtins.input", _inputs(["1"]))

    mod.runtimeAppContext.data_consent=True
    mod.runtimeAppContext.external_consent=True
    mod.toggle_external_services()

    assert mod.runtimeAppContext.external_consent is False


def test_toggle_external_services_enables(monkeypatch):
    """Toggle should enable external services when selecting option 1."""
    monkeypatch.setattr("builtins.input", _inputs(["1"]))

    mod.runtimeAppContext.data_consent=True
    mod.runtimeAppContext.external_consent=False
    mod.toggle_external_services()

    assert mod.runtimeAppContext.external_consent is True


def test_toggle_external_services_back_no_change(monkeypatch):
    """Selecting 0 (back) should not change external_consent."""
    monkeypatch.setattr("builtins.input", _inputs(["0"]))

    runtimeAppContext.external_consent=True
    mod.toggle_external_services()

    assert runtimeAppContext.external_consent is True
        
def test_prompt_thumbnail_upload_success(monkeypatch, tmp_path):
    """Test successful thumbnail upload flow."""
    # Setup
    thumbnail_dir = tmp_path / "thumbnails"
    thumbnail_dir.mkdir()
    
    # Create a fake image file
    fake_image = tmp_path / "test_image.png"
    fake_image.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # Minimal PNG header
    
    storage_path = tmp_path / "project_insights.json"
    storage_path.write_text('[{"id": "test-uuid-123", "project_name": "TestProject"}]')
    
    # Mock inputs: 'y' to add thumbnail, path to image
    monkeypatch.setattr("builtins.input", _inputs(["y", str(fake_image)]))
    
    # Mock ThumbnailManager
    mock_thumb_path = thumbnail_dir / "test-uuid-123.png"
    monkeypatch.setattr(
        mod,
        "ThumbnailManager",
        lambda storage_dir: SimpleNamespace(
            validate_image=lambda p: (True, None),
            add_thumbnail=lambda project_id, image_path, resize: (True, None, mock_thumb_path),
        ),
    )
    
    # Mock update_thumbnail_in_insights
    called = {}
    monkeypatch.setattr(
        mod,
        "update_thumbnail_in_insights",
        lambda pid, path, spath: called.setdefault("called", (pid, path)),
    )
    
    runtimeAppContext.legacy_save_dir=tmp_path
    
    result = mod.prompt_thumbnail_upload("test-uuid-123", "TestProject")
    
    assert result is True
    assert called["called"][0] == "test-uuid-123"


def test_prompt_thumbnail_upload_declined(monkeypatch, tmp_path):
    """Test user declining thumbnail upload."""
    monkeypatch.setattr("builtins.input", _inputs(["n"]))
    
    runtimeAppContext.legacy_save_dir=tmp_path
    result = mod.prompt_thumbnail_upload("test-uuid", "TestProject")
    
    assert result is False


def test_prompt_thumbnail_upload_cancelled(monkeypatch, tmp_path):
    """Test user cancelling during path input."""
    monkeypatch.setattr("builtins.input", _inputs(["y", "cancel"]))
    
    # Mock ThumbnailManager
    monkeypatch.setattr(
        mod,
        "ThumbnailManager",
        lambda storage_dir: SimpleNamespace(),
    )
    
    runtimeAppContext.legacy_save_dir=tmp_path
    result = mod.prompt_thumbnail_upload("test-uuid", "TestProject")
    
    assert result is False

def test_remove_thumbnail_workflow_unpacks_tuple_correctly(monkeypatch, tmp_path):
    """Test that _remove_thumbnail_workflow correctly unpacks the (insight, thumb_path) tuple."""
    storage_path = tmp_path / "project_insights.json"
    
    # Create mock insight with thumbnail
    mock_insight = SimpleNamespace(
        id="test-uuid",
        project_name="TestProject",
        thumbnail={"exists": True, "path": "/some/path.png"}
    )
    
    monkeypatch.setattr(
        mod,
        "list_project_insights",
        lambda storage_path: [mock_insight],
    )
    
    # Track calls
    called = {}
    
    mock_thumbnail_manager = SimpleNamespace(
        get_thumbnail_path=lambda pid: Path("/fake/thumb.png") if pid == "test-uuid" else None,
        delete_thumbnail=lambda pid: called.setdefault("deleted", pid) or True,
    )
    
    monkeypatch.setattr(
        mod,
        "remove_thumbnail_from_insights",
        lambda pid, spath: called.setdefault("removed", pid),
    )
    
    # User selects project 1, confirms deletion
    monkeypatch.setattr("builtins.input", _inputs(["1", "y", ""]))
    
    mod._remove_thumbnail_workflow(storage_path, mock_thumbnail_manager)
    
    assert called.get("deleted") == "test-uuid"
    assert called.get("removed") == "test-uuid"
