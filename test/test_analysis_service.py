import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Validates analysis orchestration, export, and consent-aware OOP analysis helpers.
import src.analysis_service as mod


def test_convert_datetime_to_string_handles_nested():
    now = datetime.datetime(2025, 1, 1, 12, 0, 0)
    delta = datetime.timedelta(days=2, hours=3)
    data = {
        "when": now,
        "delta": delta,
        "items": [now, delta, {"nested": now}],
    }
    out = mod.convert_datetime_to_string(data)
    assert out["when"] == "2025-01-01 12:00:00"
    assert out["delta"] == "2 days, 3:00:00"
    assert out["items"][0] == "2025-01-01 12:00:00"
    assert out["items"][1] == "2 days, 3:00:00"
    assert out["items"][2]["nested"] == "2025-01-01 12:00:00"


def test_extract_if_zip_raises_on_error(monkeypatch):
    class FakeExtractor:
        def __init__(self, path):
            self.path = path

        def runExtraction(self):
            return "Error: bad zip"

    monkeypatch.setattr(mod, "extractInfo", lambda path: FakeExtractor(path))

    with pytest.raises(ValueError):
        mod.extract_if_zip(Path("bad.zip"))


def test_export_json_saves_and_inserts_db_when_user_confirms(tmp_path, monkeypatch):
    ctx = SimpleNamespace(
        default_save_dir=tmp_path / "saves",
        store=SimpleNamespace(insert_json=MagicMock(return_value=42)),
    )

    captured = {}

    class FakeSaver:
        def saveAnalysis(self, project_name, analysis, out_dir):
            captured["project_name"] = project_name
            captured["analysis"] = analysis
            captured["out_dir"] = out_dir

    monkeypatch.setattr(mod, "SaveFileAnalysisAsJSON", lambda: FakeSaver())
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    analysis = {"ok": True}
    mod.export_json("DemoProj", analysis, ctx)

    assert (ctx.default_save_dir).exists()
    assert captured["project_name"] == "DemoProj"
    assert captured["analysis"]["ok"] is True
    assert Path(captured["out_dir"]).name == "saves"
    ctx.store.insert_json.assert_called_once()


def test_oop_analysis_runs_when_external_disabled(tmp_path, monkeypatch):
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
    called = {}
    monkeypatch.setattr(mod, "pretty_print_oop_report", lambda m: called.setdefault("printed", m))

    resume = SimpleNamespace(languages=["Python"])
    result = mod.oop_analysis(Path("/tmp/project"), resume, cfg_dir)

    assert result == metrics
    assert called["printed"] == metrics


def test_oop_analysis_skips_when_external_enabled(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "User_config_files"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "UserConfigs.json").write_text('{"consented": {"external": true}}')

    spy = MagicMock()
    monkeypatch.setattr(mod, "MultiLangOrchestrator", spy)

    resume = SimpleNamespace(languages=["Python"])
    result = mod.oop_analysis(Path("/tmp/project"), resume, cfg_dir)

    assert result is None
    spy.assert_not_called()


def test_analyze_project_builds_analysis_and_exports(tmp_path, monkeypatch):
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
    monkeypatch.setattr(mod, "estimate_duration", lambda hierarchy: "4 days")
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
    monkeypatch.setattr(
        mod,
        "oop_analysis",
        lambda root, resume, legacy: {"score": {"oop_score": 0.75}},
    )

    captured = {}
    monkeypatch.setattr(
        mod,
        "export_json",
        lambda project_name, analysis, ctx_obj: captured.update(
            {"project_name": project_name, "analysis": analysis, "ctx": ctx_obj}
        ),
    )

    mod.analyze_project(tmp_path, ctx)

    assert captured["project_name"] == tmp_path.name
    assert captured["ctx"] is ctx


def test_analyze_project_honors_project_label(tmp_path, monkeypatch):
    ctx = SimpleNamespace(
        default_save_dir=tmp_path / "saves",
        legacy_save_dir=tmp_path / "legacy",
        store=SimpleNamespace(),
    )

    class FakeExtractor:
        def __init__(self, root):
            self.root = root

        def file_hierarchy(self):
            return {}

    monkeypatch.setattr(mod, "FileMetadataExtractor", FakeExtractor)
    monkeypatch.setattr(mod, "estimate_duration", lambda hierarchy: "1 day")

    captured = {}

    def fake_resume(root, project_name):
        captured["resume_name"] = project_name
        return SimpleNamespace(
            project_name=project_name,
            summary="Summary",
            highlights=[],
            project_type="solo",
            detection_mode="local",
            languages=[],
            frameworks=[],
            skills=[],
            framework_sources={},
        )

    monkeypatch.setattr(mod, "generate_resume_item", fake_resume)
    monkeypatch.setattr(mod, "contribution_summary", lambda root: {})
    monkeypatch.setattr(
        mod,
        "record_project_insight",
        lambda analysis, contributors=None: SimpleNamespace(
            id=1, project_name=analysis["resume_item"]["project_name"]
        ),
    )
    monkeypatch.setattr(mod, "oop_analysis", lambda root, resume, legacy: None)
    monkeypatch.setattr(
        mod,
        "export_json",
        lambda project_name, analysis, ctx_obj: captured.setdefault(
            "export_name", project_name
        ),
    )

    mod.analyze_project(tmp_path, ctx, project_label="CustomZip")

    assert captured["resume_name"] == "CustomZip"
    assert captured["export_name"] == "CustomZip"
