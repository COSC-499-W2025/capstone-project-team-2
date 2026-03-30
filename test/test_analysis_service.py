import datetime
from os.path import exists
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import os
import shutil
from src.core.analysis_service import analyze_project, extract_if_zip, oop_analysis

from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.API.analysis_API import analysisRouter

# Validates analysis orchestration, export, and consent-aware OOP analysis helpers.
import src.core.analysis_service as mod

from src.core.app_context import runtimeAppContext

def _fake_resume(project_name=None, root=None):
    """Helper: returns a SimpleNamespace matching the new ResumeItem shape."""
    return SimpleNamespace(
        project_name=project_name or (root.name if root else "project"),
        summary="Built project",
        highlights=["h1"],
        project_type="collaborative",
        detection_mode="local",
        languages=["Python"],
        frameworks=[],
        skills=[],
        framework_sources={},
        evidence={
            "duration": None,
            "doc_metrics": [],
            "doc_key_points": [],
            "doc_types_found": [],
            "test_file_count": 0,
            "contributor_count": 0,
            "contributor_names": [],
            "contributor_breakdown": {},
        },
    )

def test_export_if_zip():
    """
    Checks that extract_if_zip() extracts and returns the directory extracted to
    """
    path = Path(os.getcwd()).absolute().resolve() / "test" / "TestZIPs" / "TESTING.zip"
    extracted_path = mod.extract_if_zip(path)
    assert exists(extracted_path)
    shutil.rmtree(extracted_path)
    
def test_nonexistent_zip_extraction():
    """
    Check that nonexistent zip files raise an exception.
    """
    try:
        extract_if_zip(Path("/fake/path/to/file.zip"))
        assert False, "Should have raised an exception"
    except Exception as e:
        print(f"Test PASSED - Got exception: {type(e).__name__}: {e}")
        assert True
        
def test_analyse_nonexistant_folder():
    """
    Check that analyzing a non-existent folder raises an exception.
    """
    try:
        analyze_project(Path("/fake/project/path"))
        assert False, "Should have raised an exception"
    except Exception as e:
        print(f"Test PASSED - Got exception: {type(e).__name__}: {e}")
        assert True

def test_export_json_saves_and_inserts_db_when_user_confirms(tmp_path, monkeypatch):
    """
    Check that export saves files and writes to the DB.
    """
    captured = {}

    class FakeSaver:
        def saveAnalysis(self, project_name, analysis, out_dir):
            captured["project_name"] = project_name
            captured["analysis"] = analysis
            captured["out_dir"] = out_dir

    monkeypatch.setattr(mod, "SaveFileAnalysisAsJSON", lambda: FakeSaver())
    monkeypatch.setattr(
        runtimeAppContext,
        "store",
        SimpleNamespace(insert_json=lambda filename, analysis: 1),
    )

    analysis = {"ok": True}
    result = mod.export_json("DemoProj", analysis)

    assert (runtimeAppContext.default_save_dir).exists()
    assert captured["project_name"] == "DemoProj"
    assert captured["analysis"]["ok"] is True
    assert result["skipped"] is False
    assert "snapshots" in result

    monkeypatch.setattr(mod, "SaveFileAnalysisAsJSON", lambda: FakeSaver())
    
    def failing_insert(filename, analysis):
        raise Exception("Database connection failed")
    
    monkeypatch.setattr(
        runtimeAppContext,
        "store",
        SimpleNamespace(insert_json=failing_insert),
    )

    try:
        mod.export_json("DemoProj", {"ok": True})
        assert False, "Should have raised an exception"
    except Exception as e:
        print(f"Test PASSED - Got exception: {type(e).__name__}: {e}")
        assert True


def test_export_json_sanitizes_filename_stem(monkeypatch):
    """Unsafe path characters in project names must be removed before persistence."""
    captured = {}

    class FakeSaver:
        def saveAnalysis(self, project_name, analysis, out_dir):
            captured["project_name"] = project_name

    def fake_insert(filename, analysis):
        captured["filename"] = filename
        return ("ok", False)

    monkeypatch.setattr(mod, "SaveFileAnalysisAsJSON", lambda: FakeSaver())
    monkeypatch.setattr(
        runtimeAppContext,
        "store",
        SimpleNamespace(insert_json=fake_insert),
    )

    result = mod.export_json("../Sam/http", {"ok": True})
    assert result["skipped"] is False
    assert captured["project_name"] == "Sam_http"
    assert captured["filename"] == "Sam_http.json"
        
        
def test_oop_analysis_runs(tmp_path, monkeypatch):
    """Check that local OOP analysis runs."""
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
            def get_duration_human(self):
                return "Unknown"

        class FakeDocAnalyzer:
            def __init__(self, root):
                self.root = root
            def analyze(self):
                return {"documents": []}

        captured = {}

        def fake_oop_analysis(root, languages_found):
            captured["languages_found"] = languages_found
            return {"score": {"oop_score": 0.5}}

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with (
                patch.object(mod, "FileMetadataExtractor", FakeExtractor),
                patch.object(mod, "Project_Duration_Estimator", FakeDurationEstimator),
                patch.object(mod, "DocumentAnalyzer", FakeDocAnalyzer),
                patch.object(
                    mod,
                    "generate_resume_item",
                    lambda root, project_name=None, doc_analysis=None, contrib_summary_data=None: _fake_resume(project_name=project_name, root=root),
                ),
                patch.object(mod, "contribution_summary", lambda root: None),
                patch.object(mod, "load_portfolio_showcase", lambda display_name: None),
                patch.object(mod, "build_portfolio_showcase", lambda data, yaml: None),
                patch.object(mod, "export_json", lambda project_name, analysis: {"skipped": False, "snapshots": []}),
                patch.object(mod, "record_project_insight", lambda analysis, contributors=None, snapshot_label=None: None),
                patch.object(mod, "deduplicate_project", lambda root, index_path, remove_duplicates=True: SimpleNamespace(
                    unique_files=1,
                    duplicate_files=0,
                    duplicates=[],
                    index_size=1,
                    removed=0,
                )),
                patch.object(mod, "detect_project_stack", lambda root: {"languages": ["C++"]}),
                patch.object(mod, "oop_analysis", fake_oop_analysis),
            ):
                mod.analyze_project(root)

        self.assertEqual(captured["languages_found"], ["C++", "Python"])

def test_export_json_appends_snapshots_and_merges_skills(tmp_path, monkeypatch):
    """Ensure incremental uploads append snapshots and union skills/frameworks."""
    import json
    save_dir = tmp_path / "saves"
    monkeypatch.setattr(mod.runtimeAppContext, "default_save_dir", save_dir)
    monkeypatch.setattr(mod.runtimeAppContext, "store", SimpleNamespace(insert_json=lambda *args, **kwargs: None))

    base_analysis = {
        "project_root": "/p1",
        "duration_estimate": "1 day",
        "resume_item": {
            "project_name": "Demo",
            "skills": ["Python"],
            "frameworks": ["FastAPI"],
        },
        "dedup": {},
    }

    mod.export_json("Demo", base_analysis)

    second_analysis = {
        "project_root": "/p1",
        "duration_estimate": "2 days",
        "resume_item": {
            "project_name": "Demo",
            "skills": ["Docker"],
            "frameworks": ["FastAPI", "React"],
        },
        "dedup": {},
    }

    meta = mod.export_json("Demo", second_analysis)
    saved = json.loads((save_dir / "Demo.json").read_text())

    assert meta["snapshots"]
    assert len(saved.get("snapshots", [])) == 2
    assert set(saved["resume_item"]["skills"]) == {"Python", "Docker"}
    assert set(saved["resume_item"]["frameworks"]) == {"FastAPI", "React"}

def test_oop_analysis_raises_on_failure(monkeypatch):
    """OOP is critical: if supported languages exist and analysis fails, it should raise."""

    class FailingOrchestrator:
        def __init__(self, root):
            pass
        def analyze(self):
            raise RuntimeError("OOP failed")

    monkeypatch.setattr(mod, "MultiLangOrchestrator", FailingOrchestrator)

    with pytest.raises(RuntimeError):
        mod.oop_analysis(Path("/tmp/project"), ["Python"])

def test_analyze_project_builds_analysis_and_exports(tmp_path, monkeypatch):
    """Check that analysis builds results and triggers export."""
    class FakeExtractor:
        def __init__(self, root):
            self.root = root
        def file_hierarchy(self):
            return {"type": "DIR", "children": []}

    class FakeDurationEstimator:
        def __init__(self, hierarchy):
            self.hierarchy = hierarchy
        def get_duration_human(self):
            return "Unknown"

    class FakeDocAnalyzer:
        def __init__(self, root):
            self.root = root
        def analyze(self):
            return {"documents": []}

    monkeypatch.setattr(mod, "FileMetadataExtractor", FakeExtractor)
    monkeypatch.setattr(mod, "Project_Duration_Estimator", FakeDurationEstimator)
    monkeypatch.setattr(mod, "DocumentAnalyzer", FakeDocAnalyzer)
    monkeypatch.setattr(
        mod,
        "generate_resume_item",
        lambda root, project_name=None, doc_analysis=None, contrib_summary_data=None: _fake_resume(project_name=project_name, root=root),
    )
    monkeypatch.setattr(
        mod,
        "contribution_summary",
        lambda root: {"metric": "files", "contributors": {"Alice": {"file_count": 2, "percentage": "100%"}}},
    )
    monkeypatch.setattr(
        mod,
        "record_project_insight",
        lambda analysis, contributors=None, snapshot_label=None: SimpleNamespace(id=1, project_name=analysis["resume_item"]["project_name"]),
    )
    monkeypatch.setattr(mod, "load_portfolio_showcase", lambda display_name: None)
    monkeypatch.setattr(mod, "build_portfolio_showcase", lambda data, yaml: None)
    monkeypatch.setattr(mod, "detect_project_stack", lambda root: {"languages": []})
    monkeypatch.setattr(
        mod,
        "deduplicate_project",
        lambda root, index_path, remove_duplicates=True: SimpleNamespace(
            unique_files=1,
            duplicate_files=0,
            duplicates=[],
            index_size=1,
            removed=0,
        ),
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
    
def test_analyze_project_backfills_duration_into_evidence(monkeypatch, tmp_path):
    """Duration computed by estimator should be copied into resume_item.evidence['duration']."""    
    captured = {}

    class FakeExtractor:
        def __init__(self, root): pass
        def file_hierarchy(self): return {"type": "DIR", "children": []}

    class FakeDurationEstimator:
        def __init__(self, hierarchy): pass
        def get_duration_human(self): return "5 months"

    class FakeDocAnalyzer:
        def __init__(self, root): pass
        def analyze(self): return {"documents": []}

    def fake_export(project_name, analysis):
        captured["analysis"] = analysis
        return {"skipped": False, "snapshots": []}

    monkeypatch.setattr(mod, "FileMetadataExtractor", FakeExtractor)
    monkeypatch.setattr(mod, "Project_Duration_Estimator", FakeDurationEstimator)
    monkeypatch.setattr(mod, "DocumentAnalyzer", FakeDocAnalyzer)

    # resume.evidence.duration starts None
    resume_obj = _fake_resume(project_name="X", root=tmp_path)
    monkeypatch.setattr(mod, "generate_resume_item", lambda *args, **kwargs: resume_obj)

    monkeypatch.setattr(mod, "contribution_summary", lambda root: None)
    monkeypatch.setattr(mod, "load_portfolio_showcase", lambda display_name: None)
    monkeypatch.setattr(mod, "build_portfolio_showcase", lambda data, yaml: None)
    monkeypatch.setattr(mod, "record_project_insight", lambda *a, **k: None)
    monkeypatch.setattr(mod, "deduplicate_project", lambda *a, **k: SimpleNamespace(
        unique_files=1, duplicate_files=0, duplicates=[], index_size=1, removed=0
    ))
    monkeypatch.setattr(mod, "detect_project_stack", lambda root: {"languages": []})
    monkeypatch.setattr(mod, "oop_analysis", lambda root, langs: None)
    monkeypatch.setattr(mod, "export_json", fake_export)

    mod.analyze_project(tmp_path)

    evidence = captured["analysis"]["resume_item"]["evidence"]
    assert evidence["duration"] == "5 months"
