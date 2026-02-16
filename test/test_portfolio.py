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

    # Mock input to skip PDF generation prompts
    inputs = iter(["n"])   # sequence of answers
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    # Verify portfolio showcase is displayed with OOP score
    assert "PORTFOLIO SHOWCASE" in out
    assert "OOP score: 0.8" in out


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
    # Mock input to skip PDF generation prompts
    inputs = iter(["n"])   # sequence of answers
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    assert "PROJECT: DemoProj" in out
    assert "One-Sentence Summary: Summary" in out    
    
def test_display_portfolio_default_enter_skips_pdf(monkeypatch, tmp_path, capsys):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text('{"consented": {"external": false}}')

    data = {
        "resume_item": {"project_name": "Demo", "summary": "Demo"},
        "oop_analysis": {"score": {"oop_score": 0.5}},
    }
    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps(data))

    # User presses ENTER (empty string)
    inputs = iter([""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    # Should show portfolio but not ask for filename
    assert "PORTFOLIO SHOWCASE" in out
    assert "Enter the name of the PDF" not in out
    
def test_display_portfolio_reprompts_on_invalid_input(monkeypatch, tmp_path, capsys):
    ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
    ctx.legacy_save_dir.mkdir(parents=True)
    (ctx.legacy_save_dir / "UserConfigs.json").write_text('{"consented": {"external": false}}')

    data = {
        "resume_item": {"project_name": "Demo", "summary": "Demo"},
        "oop_analysis": {"score": {"oop_score": 0.5}},
    }
    file_path = tmp_path / "analysis.json"
    file_path.write_text(mod.json.dumps(data))

    # First invalid, then valid "n"
    inputs = iter(["maybe", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mod.display_portfolio_and_generate_pdf(file_path, ctx)
    out = capsys.readouterr().out

    assert "[WARN] Please enter only 'y' or 'n'." in out
    
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

    # Say yes, then provide filename
    inputs = iter(["y", "TestPortfolio"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    try:
        mod.display_portfolio_and_generate_pdf(file_path, ctx)
    except Exception:
        pass  

    out = capsys.readouterr().out

    assert "PORTFOLIO SHOWCASE" in out
    assert "[INFO] Generating portfolio PDF using RenderCV..." in out


