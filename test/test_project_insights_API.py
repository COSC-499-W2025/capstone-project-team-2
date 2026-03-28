from fastapi.testclient import TestClient
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
        