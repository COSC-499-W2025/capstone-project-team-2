from pathlib import Path
from types import SimpleNamespace

import pytest

# Exercises portfolio display paths for consent on/off.
import src.reporting.portfolio as mod


def test_display_portfolio_external_disabled_uses_saved_oop(monkeypatch, tmp_path, capsys):
    """Check that saved OOP metrics are used without consent.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.
        tmp_path: Pytest fixture providing a temporary directory.
        capsys: Pytest fixture for capturing stdout/stderr.

    Returns:
        None: Assertions validate output and metrics usage.
    """
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

    result = mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    # Verify portfolio showcase is displayed with OOP score
    assert "PORTFOLIO SHOWCASE" in out
    assert "OOP score: 0.8" in out
    assert result["status"] == "ok"
    assert result["pdf_generated"] is False


def test_display_portfolio_external_enabled_calls_generator(monkeypatch, tmp_path, capsys):
    """Check that resume generation runs with consent.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.
        tmp_path: Pytest fixture providing a temporary directory.
        capsys: Pytest fixture for capturing stdout/stderr.

    Returns:
        None: Assertions validate generated output.
    """
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
    result = mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    assert "PROJECT: DemoProj" in out
    assert "One-Sentence Summary: Summary" in out
    assert result["status"] == "ok"
    assert result["pdf_generated"] is False
    
def test_display_portfolio_default_skips_pdf(tmp_path, capsys):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text('{"consented": {"external": false}}')

    data = {
        "resume_item": {"project_name": "Demo", "summary": "Demo"},
        "oop_analysis": {"score": {"oop_score": 0.5}},
    }
    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps(data))

    result = mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    assert "PORTFOLIO SHOWCASE" in out
    assert result["status"] == "ok"
    assert result["pdf_generated"] is False


def test_display_portfolio_pdf_errors_when_dir_missing(tmp_path, capsys):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text('{"consented": {"external": false}}')

    data = {
        "resume_item": {"project_name": "Demo", "summary": "Demo"},
        "oop_analysis": {"score": {"oop_score": 0.5}},
    }
    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps(data))

    result = mod.display_portfolio_and_generate_pdf(
        file_path,
        ctx,
        generate_pdf=True,
        custom_output_dir=tmp_path / "missing_out",
    )
    assert result["status"] == "error"
    assert "Path not found" in result["detail"]


def test_display_portfolio_yes_triggers_pdf_flow(monkeypatch, tmp_path, capsys):
    ctx = SimpleNamespace(
        legacy_save_dir=tmp_path / "User_config_files",
        external_consent=False,
    )
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text(
        '{"consented": {"external": false}}'
    )

    data = {
        "resume_item": {"project_name": "Demo", "summary": "Demo"},
        "oop_analysis": {"score": {"oop_score": 0.5}},
    }
    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps(data))

    class FakeService:
        def __init__(self, name):
            self.name = name
        def add_portfolio(self, _ps):
            return None
        def render_portfolio_pdf(self):
            fake_pdf = tmp_path / "rendercv.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            return ("ok", fake_pdf)
    monkeypatch.setattr(mod, "PortfolioRenderCVService", FakeService)

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    result = mod.display_portfolio_and_generate_pdf(
        file_path,
        ctx,
        generate_pdf=True,
        output_name="TestPortfolio",
        custom_output_dir=output_dir,
    )

    out = capsys.readouterr().out

    assert "PORTFOLIO SHOWCASE" in out
    assert "[INFO] Generating portfolio PDF using RenderCV..." in out
    assert result["status"] == "ok"
    assert result["pdf_generated"] is True

