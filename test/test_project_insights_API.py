from fastapi.testclient import TestClient
import json
import shutil

from src.API.project_insights_API import *
from src.API.general_API import app
from src.core.app_context import create_app_context

from src.analysis.insight_helpers import parse_date

def test_return_project_insights_chronological():
    """
    Ensures that the correct amount of projects are returned and that they are in chronological order.
    """
    root_folder = Path(__file__).absolute().resolve().parents[1]
    runtimeAppContext.legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = runtimeAppContext.legacy_save_dir / "project_insights" #ensures temp paths from other tests don't leak in
    testclient = TestClient(app)
    storage_path = Path(runtimeAppContext.legacy_save_dir / "project_insights.json")
    test_path = Path(runtimeAppContext.legacy_save_dir.parent / "test" / "test_files" / "project_insights.json")
    shutil.copy(test_path, storage_path)
    response = testclient.get("/insights/projects")
    dicts = response.json()
    assert response.status_code == 200
    assert len(dicts) == 3
    last_date = None
    for d in dicts:
        this_date = parse_date(d["analyzed_at"])
        if last_date:
            assert last_date <= this_date
        last_date = this_date

def test_return_skill_insights_chronological():
    """
    Ensures the correct amount of projects are returned and that they are in chronological order of skills.
    """
    root_folder = Path(__file__).absolute().resolve().parents[1]
    runtimeAppContext.legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = runtimeAppContext.legacy_save_dir / "project_insights" #ensures temp paths from other tests don't leak in
    testclient = TestClient(app)
    storage_path = Path(runtimeAppContext.legacy_save_dir / "project_insights.json")
    test_path = Path(runtimeAppContext.legacy_save_dir.parent / "test" / "test_files" / "project_insights.json")
    shutil.copy(test_path, storage_path)
    response = testclient.get("/insights/skills")
    dicts = response.json()
    assert response.status_code == 200
    assert len(dicts) == 3
    last_date = None
    for d in dicts:
        this_date = parse_date(d["analyzed_at"])
        if last_date:
            assert last_date <= this_date
        last_date = this_date


def test_return_top_project_histories_unique_projects():
    """
    Ensures top project history endpoint collapses snapshots by project name and
    returns evolution metadata.
    """
    root_folder = Path(__file__).absolute().resolve().parents[1]
    runtimeAppContext.legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = runtimeAppContext.legacy_save_dir / "project_insights"
    testclient = TestClient(app)
    storage_path = Path(runtimeAppContext.legacy_save_dir / "project_insights.json")

    sample = [
        {
            "id": "alpha-1",
            "project_name": "Alpha",
            "summary": "Initial alpha snapshot.",
            "analyzed_at": "2025-05-01T00:00:00+00:00",
            "languages": ["Python"],
            "skills": ["Python"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 3},
            "file_analysis": {"file_count": 1},
        },
        {
            "id": "alpha-2",
            "project_name": "Alpha",
            "summary": "Expanded alpha snapshot.",
            "analyzed_at": "2025-05-02T00:00:00+00:00",
            "languages": ["Python", "TypeScript"],
            "skills": ["Python", "TypeScript"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 8},
            "file_analysis": {"file_count": 3},
        },
        {
            "id": "beta-1",
            "project_name": "Beta",
            "summary": "Only beta snapshot.",
            "analyzed_at": "2025-05-03T00:00:00+00:00",
            "languages": ["Go"],
            "skills": ["Go", "Docker"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 5},
            "file_analysis": {"file_count": 2},
        },
    ]
    storage_path.write_text(json.dumps(sample), encoding="utf-8")

    response = testclient.get("/insights/top-projects")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 2
    assert [entry["project_name"] for entry in body] == ["Alpha", "Beta"]
    assert body[0]["snapshot_count"] == 2
    assert body[0]["evolution"]["new_languages"] == ["TypeScript"]
    assert body[0]["latest"]["summary"] == "Expanded alpha snapshot."


def test_return_top_project_histories_respects_top_n():
    """Ensures the top-project history endpoint respects the top_n query parameter."""
    root_folder = Path(__file__).absolute().resolve().parents[1]
    runtimeAppContext.legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = runtimeAppContext.legacy_save_dir / "project_insights"
    testclient = TestClient(app)
    storage_path = Path(runtimeAppContext.legacy_save_dir / "project_insights.json")

    sample = [
        {
            "id": "one-1",
            "project_name": "One",
            "summary": "One summary.",
            "analyzed_at": "2025-05-01T00:00:00+00:00",
            "languages": ["Python"],
            "skills": ["Python"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 10},
            "file_analysis": {"file_count": 1},
        },
        {
            "id": "two-1",
            "project_name": "Two",
            "summary": "Two summary.",
            "analyzed_at": "2025-05-02T00:00:00+00:00",
            "languages": ["Go"],
            "skills": ["Go"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 2},
            "file_analysis": {"file_count": 1},
        },
    ]
    storage_path.write_text(json.dumps(sample), encoding="utf-8")

    response = testclient.get("/insights/top-projects?top_n=1")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["project_name"] == "One"


def test_return_top_project_histories_prefers_skills_then_recency_on_ties():
    """Ensures top-project endpoint breaks equal contribution ties by skills, then recency."""
    root_folder = Path(__file__).absolute().resolve().parents[1]
    runtimeAppContext.legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = runtimeAppContext.legacy_save_dir / "project_insights"
    testclient = TestClient(app)
    storage_path = Path(runtimeAppContext.legacy_save_dir / "project_insights.json")

    sample = [
        {
            "id": "older-1",
            "project_name": "OlderNoSkills",
            "summary": "Older project without detected skills.",
            "analyzed_at": "2025-05-01T00:00:00+00:00",
            "languages": [],
            "skills": [],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 5},
            "file_analysis": {"file_count": 1},
        },
        {
            "id": "newer-1",
            "project_name": "NewerPython",
            "summary": "Newer project with Python skill.",
            "analyzed_at": "2025-05-03T00:00:00+00:00",
            "languages": ["Python"],
            "skills": ["Python"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 5},
            "file_analysis": {"file_count": 1},
        },
        {
            "id": "newest-1",
            "project_name": "NewestPython",
            "summary": "Newest project with same skill count.",
            "analyzed_at": "2025-05-04T00:00:00+00:00",
            "languages": ["Python"],
            "skills": ["Python"],
            "project_type": "collaborative",
            "stats": {"top_contribution_count": 5},
            "file_analysis": {"file_count": 1},
        },
    ]
    storage_path.write_text(json.dumps(sample), encoding="utf-8")

    response = testclient.get("/insights/top-projects")
    body = response.json()

    assert response.status_code == 200
    assert [entry["project_name"] for entry in body] == ["NewestPython", "NewerPython", "OlderNoSkills"]
