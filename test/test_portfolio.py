from pathlib import Path
from types import SimpleNamespace

import pytest

# Exercises portfolio display paths for consent on/off.
import src.portfolio as mod

def test_display_portfolio_external_disabled_uses_saved_oop(monkeypatch, tmp_path, capsys):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text('{"consented": {"external": false}}')

    data = {
        "project_root": "/tmp/demo",
        "resume_item": {
            "project_type": "individual",
            "detection_mode": "local",
            "languages": ["Python"],
            "frameworks": [],
            "skills": ["Python"],
            "summary": "Demo",
        },
        "duration_estimate": "1 day",
        "oop_analysis": {"score": {"oop_score": 0.8}},
    }
    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps(data))

    called = {}
    monkeypatch.setattr(mod, "pretty_print_oop_report", lambda metrics: called.setdefault("metrics", metrics))

    mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    assert "PROJECT: analysis.json" in out
    assert called["metrics"]["score"]["oop_score"] == 0.8

def test_display_portfolio_external_enabled_calls_generator(monkeypatch, tmp_path, capsys):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=True)
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text('{"consented": {"external": true}}')

    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps({"project_root": "/tmp/demo"}))

    generated = SimpleNamespace(
        project_title="DemoProj",
        one_sentence_summary="Summary",
        key_skills_used=["Python"],
        tech_stack=["FastAPI"],
        oop_principles_detected={},
    )
    class FakeResume:
        def __init__(self, root):
            self.root = root

        def generate(self, saveToJson=False):
            return generated

    monkeypatch.setattr(mod, "GenerateProjectResume", FakeResume)
    monkeypatch.setattr(mod, "prompt_export_formats", lambda label: [])

    mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    assert "PROJECT: DemoProj" in out
    assert "One-Sentence Summary: Summary" in out

def test_display_portfolio_exports_selected_formats(monkeypatch, tmp_path):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=True)
    ctx.legacy_save_dir.mkdir(parents=True)

    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps({"project_root": "/tmp/demo"}))

    generated = SimpleNamespace(
        project_title="DemoProj",
        one_sentence_summary="Summary",
        key_skills_used=["Python"],
        tech_stack=["FastAPI"],
        oop_principles_detected={
            "abstraction": SimpleNamespace(
                present=True,
                description="Uses classes",
                code_snippets=[],
            )
        },
    )

    class FakeResume:
        def __init__(self, root):
            self.root = root

        def generate(self, saveToJson=False):
            return generated

    monkeypatch.setattr(mod, "GenerateProjectResume", FakeResume)
    monkeypatch.setattr(mod, "prompt_export_formats", lambda label: ["html", "md"])

    called = {}

    def fake_export(item, ctx, artifact, formats, document_title, include_resume_line_pdf=False):
        called["artifact"] = artifact
        called["formats"] = formats
        called["title"] = document_title
        called["include_resume_line"] = include_resume_line_pdf
        return tmp_path, [tmp_path / "portfolio.html", tmp_path / "portfolio.md"]

    monkeypatch.setattr(mod, "export_resume_item", fake_export)

    mod.display_portfolio_and_generate_pdf(file_path, ctx)

    assert called["artifact"] == "portfolio"
    assert called["formats"] == ["html", "md"]
    assert called["title"] == "Portfolio"
    assert called["include_resume_line"] is True
