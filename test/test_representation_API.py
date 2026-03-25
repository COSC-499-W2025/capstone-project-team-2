"""Tests for user representation preference endpoints."""
import json
from pathlib import Path
from typing import Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.API.representation_API import representationRouter
from src.reporting import representation_preferences as prefs

@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> TestClient:
    """Provide a test client with preferences redirected to temp storage."""

    pref_path = tmp_path / "representation_preferences.json"
    monkeypatch.setattr(prefs, "PREFERENCES_PATH", pref_path)
    # ensure insights default path is empty temp location
    from src.reporting import project_insights
    empty_insights = tmp_path / "project_insights.json"
    monkeypatch.setattr(project_insights, "DEFAULT_STORAGE", empty_insights)

    app = FastAPI()
    app.include_router(representationRouter)
    return TestClient(app)

def _read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))

def test_get_preferences_defaults(client: TestClient, tmp_path: Path):
    """
    Ensure defaults are returned when no prefs file exists.

    Args: client (TestClient): FastAPI test client.
          tmp_path (Path): Temporary directory provided by pytest.
    """
    resp = client.get("/representation/preferences")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_order"] == []
    assert data["comparison_attributes"]  # default list present

def test_set_preferences_and_persist(client: TestClient, tmp_path: Path):
    """
    Verify updating preferences persists to disk.

    Args: client (TestClient): FastAPI test client.
         tmp_path (Path): Temporary directory provided by pytest.
    """
    payload = {
        "project_order": ["B", "A"],
        "highlight_skills": ["Python"],
    }

    resp = client.post("/representation/preferences", json=payload)
    assert resp.status_code == 200
    assert resp.json()["project_order"] == ["B", "A"]

    # file persisted
    pref_file = tmp_path / "representation_preferences.json"
    assert pref_file.exists()
    disk = _read_json(pref_file)
    assert disk["highlight_skills"] == ["Python"]


def test_set_preferences_persists_project_overrides(client: TestClient, tmp_path: Path):
    """Project-level manual overrides should persist via representation preferences."""
    payload = {
        "project_overrides": {
            "Alpha": {
                "contribution_type": "team leadership",
                "duration_estimate": "8 months",
            }
        }
    }

    resp = client.post("/representation/preferences", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_overrides"]["Alpha"]["contribution_type"] == "team leadership"
    assert body["project_overrides"]["Alpha"]["duration_estimate"] == "8 months"

    pref_file = tmp_path / "representation_preferences.json"
    disk = _read_json(pref_file)
    assert disk["project_overrides"]["Alpha"]["contribution_type"] == "team leadership"
    assert disk["project_overrides"]["Alpha"]["duration_estimate"] == "8 months"

def test_projects_endpoint_empty_without_insights(client: TestClient):
    """
    Confirm /projects returns an empty payload when no insights exist.

    Args: client (TestClient): FastAPI test client.
    """
    resp = client.get("/representation/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert body["projects"] == []

def test_projects_respects_showcase_filter(client: TestClient, tmp_path: Path, monkeypatch):
    """
    Ensure showcase filter returns only showcase projects.

    Args: client (TestClient): FastAPI test client.
          tmp_path (Path): Temporary directory provided by pytest.
          monkeypatch: Pytest monkeypatch helper.
    """
    # create fake insights file
    insights_path = tmp_path / "project_insights.json"
    sample = [
        {"id": "1", "project_name": "Alpha", "summary": "", "analyzed_at": "2024-01-01T00:00:00Z"},
        {"id": "2", "project_name": "Beta", "summary": "", "analyzed_at": "2025-01-01T00:00:00Z"},
    ]
    insights_path.write_text(json.dumps(sample), encoding="utf-8")
    monkeypatch.setattr(prefs, "PREFERENCES_PATH", tmp_path / "representation_preferences.json")
    monkeypatch.setattr(prefs, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(prefs, "DEFAULT_PREFERENCES", {"project_order": [], "chronology_corrections": {}, "comparison_attributes": [], "highlight_skills": [], "showcase_projects": ["Beta"]})

    from src.reporting import project_insights

    monkeypatch.setattr(project_insights, "DEFAULT_STORAGE", insights_path)

    resp = client.get("/representation/projects?only_showcase=true")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["projects"]) == 1
    assert body["projects"][0]["project_name"] == "Beta"


def test_projects_filters_by_snapshot_label(client: TestClient, tmp_path: Path, monkeypatch):
    """Ensure snapshot_label filtering returns only matching snapshots."""
    insights_path = tmp_path / "project_insights.json"
    sample = [
        {"id": "1", "project_name": "Alpha", "summary": "", "analyzed_at": "2024-01-01T00:00:00Z", "snapshot_label": "v1"},
        {"id": "2", "project_name": "Alpha", "summary": "", "analyzed_at": "2024-02-01T00:00:00Z", "snapshot_label": "v2"},
    ]
    insights_path.write_text(json.dumps(sample), encoding="utf-8")
    monkeypatch.setattr(prefs, "PREFERENCES_PATH", tmp_path / "representation_preferences.json")
    from src.reporting import project_insights
    monkeypatch.setattr(project_insights, "DEFAULT_STORAGE", insights_path)

    resp = client.get("/representation/projects?snapshot_label=v2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["projects"]) == 1
    assert body["projects"][0]["analyzed_at"].startswith("2024-02")


def test_projects_apply_manual_overrides(client: TestClient, tmp_path: Path, monkeypatch):
    """Manual representation overrides should update contribution type and duration."""
    insights_path = tmp_path / "project_insights.json"
    sample = [
        {
            "id": "1",
            "project_name": "Alpha",
            "summary": "",
            "analyzed_at": "2024-01-01T00:00:00Z",
            "project_type": "unknown",
            "duration_estimate": "unavailable",
        }
    ]
    insights_path.write_text(json.dumps(sample), encoding="utf-8")

    pref_path = tmp_path / "representation_preferences.json"
    pref_path.write_text(
        json.dumps({
            "project_order": ["Alpha"],
            "chronology_corrections": {},
            "comparison_attributes": [],
            "highlight_skills": [],
            "showcase_projects": [],
            "project_overrides": {
                "Alpha": {
                    "contribution_type": "collaborative",
                    "duration_estimate": "6 months",
                }
            },
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(prefs, "PREFERENCES_PATH", pref_path)
    from src.reporting import project_insights
    monkeypatch.setattr(project_insights, "DEFAULT_STORAGE", insights_path)

    resp = client.get("/representation/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["projects"]) == 1
    assert body["projects"][0]["project_type"] == "collaborative"
    assert body["projects"][0]["contribution_type"] == "collaborative"
    assert body["projects"][0]["duration_estimate"] == "6 months"
