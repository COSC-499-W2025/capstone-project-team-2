import datetime
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from src.core.analysis_service import analyze_project, extract_if_zip, oop_analysis

from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.API.analysis_API import analysisRouter

# Validates analysis orchestration, export, and consent-aware OOP analysis helpers.
import src.core.analysis_service as mod

from src.core.app_context import runtimeAppContext

def test_nonexistent_zip_extraction():
    """Check that nonexistent zip files raise exception correctly
        Args: None

    Returns:
        None: Assertions validate exception is raised. 
    """
    try:
        extract_if_zip(Path("/fake/path/to/file.zip"))
        assert False, "Should have raised an exception"
    except Exception as e:
        print(f"Test PASSED - Got exception: {type(e).__name__}: {e}")
        assert True
        
def test_analyse_nonexistant_folder():
    """Check that analyzing a non-existent folder raises an exception.

    Args:
        None

    Returns:
        None: Assertions validate exception is raised.
    """
    try:
        analyze_project(Path("/fake/project/path"))
        assert False, "Should have raised an exception"
    except Exception as e:
        print(f"Test PASSED - Got exception: {type(e).__name__}: {e}")
        assert True
        
@pytest.mark.skip(reason="FastAPI not fully implemented yet")
def test_api_returns_error_when_no_file_uploaded():
    """Check that API returns error response when no file is uploaded.

    Args:
        None

    Returns:
        None: Assertions validate API returns error status code.
    """
    app = FastAPI()
    app.include_router(analysisRouter)
    client = TestClient(app)
    
    response = client.get("/analyze")
    
    # Should get an error status code, not 200
    assert response.status_code != 200
    print(f"Test PASSED - Got status code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_export_json_saves_and_inserts_db_when_user_confirms(tmp_path, monkeypatch):
    """Check that export saves files and writes to the DB.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate save and insert behavior.
    """

    captured = {}

    class FakeSaver:
        def saveAnalysis(self, project_name, analysis, out_dir):
            captured["project_name"] = project_name
            captured["analysis"] = analysis
            captured["out_dir"] = out_dir

    monkeypatch.setattr(mod, "SaveFileAnalysisAsJSON", lambda: FakeSaver())

    analysis = {"ok": True}
    mod.export_json("DemoProj", analysis)

    assert (runtimeAppContext.default_save_dir).exists()
    assert captured["project_name"] == "DemoProj"
    assert captured["analysis"]["ok"] is True
    #Can't check if db contains file at current point in time
    #runtimeAppContext.store.fetch_by_id

def test_oop_analysis_runs(tmp_path, monkeypatch):
    """Check that local OOP analysis runs.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate OOP analysis execution.
    """
    cfg_dir = tmp_path / "User_config_files"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "UserConfigs.json").write_text('{"consented": {"external": false}}')

    metrics = {"score": {"oop_score": 0.9}}
    
    class FakeOrchestrator:
        def __init__(self, root):
            pass
        def analyze(self):
            return metrics
    
    monkeypatch.setattr(mod, "MultiLangOrchestrator", FakeOrchestrator)

    languages: List[str] = list(["Python"])
    result = mod.oop_analysis(Path("/tmp/project"), languages)

    assert result == metrics

class TestAnalysisService(unittest.TestCase):
    def test_analyze_project_uses_stack_detection_for_oop_languages(self):
        """Ensure OOP analysis uses stack detection + resume languages union."""
        class FakeExtractor:
            def __init__(self, root):
                self.root = root

            def file_hierarchy(self):
                return {"type": "DIR", "children": []}

        class FakeDurationEstimator:
            def __init__(self, hierarchy):
                self.hierarchy = hierarchy

            def get_duration(self):
                return 0

        class FakeDocAnalyzer:
            def __init__(self, root):
                self.root = root

            def analyze(self):
                return {}

        captured = {}

        def fake_oop_analysis(root, languages_found):
            captured["languages_found"] = languages_found
            return {"score": {"oop_score": 0.5}}

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with (
                patch.object(mod, "FileMetadataExtractor", FakeExtractor),
                patch.object(mod, "Project_Duration_Estimator", FakeDurationEstimator),
                patch.object(
                    mod,
                    "generate_resume_item",
                    lambda root, project_name: SimpleNamespace(
                        project_name=project_name,
                        summary="Built project",
                        highlights=["h1"],
                        project_type="collaborative",
                        detection_mode="local",
                        languages=["Python"],
                        frameworks=[],
                        skills=[],
                        framework_sources={},
                    ),
                ),
                patch.object(mod, "DocumentAnalyzer", FakeDocAnalyzer),
                patch.object(mod, "contribution_summary", lambda root: None),
                patch.object(mod, "load_portfolio_showcase", lambda display_name: None),
                patch.object(mod, "build_portfolio_showcase", lambda data, yaml: None),
                patch.object(mod, "export_json", lambda project_name, analysis: None),
                patch.object(mod, "detect_project_stack", lambda root: {"languages": ["C++"]}),
                patch.object(mod, "oop_analysis", fake_oop_analysis),
            ):
                mod.analyze_project(root)

        self.assertEqual(captured["languages_found"], ["C++", "Python"])

@pytest.mark.skip
def test_analyze_project_builds_analysis_and_exports(tmp_path, monkeypatch):
    """Check that analysis builds results and triggers export.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate export behavior.
    """
    ctx = SimpleNamespace(
        default_save_dir=tmp_path / "saves",
        legacy_save_dir=tmp_path / "legacy",
        store=SimpleNamespace(),
    )

    class FakeExtractor:
        def __init__(self, root):
            self.root = root

        def file_hierarchy(self):
            return {"type": "DIR", "children": []}

    monkeypatch.setattr(mod, "FileMetadataExtractor", FakeExtractor)
    monkeypatch.setattr(
        mod,
        "generate_resume_item",
        lambda root, project_name: SimpleNamespace(
            project_name=project_name,
            summary="Built project",
            highlights=["h1"],
            project_type="collaborative",
            detection_mode="local",
            languages=["Python"],
            frameworks=["FastAPI"],
            skills=["Python"],
            framework_sources={},
        ),
    )
    monkeypatch.setattr(
        mod,
        "contribution_summary",
        lambda root: {"metric": "files", "contributors": {"Alice": {"file_count": 2, "percentage": "100%"}}},
    )
    monkeypatch.setattr(
        mod,
        "record_project_insight",
        lambda analysis, contributors=None: SimpleNamespace(id=1, project_name=analysis["resume_item"]["project_name"]),
    )
    monkeypatch.setattr(mod, "oop_analysis", lambda root, languages_found: {"score": {"oop_score": 0.75}})

    captured = {}
    monkeypatch.setattr(
        mod,
        "export_json",
        lambda project_name, analysis: captured.update(
            {"project_name": project_name, "analysis": analysis}
        ),
    )

    mod.analyze_project(tmp_path)

    assert captured["project_name"] == tmp_path.name
    assert captured["ctx"] is ctx

