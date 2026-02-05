"""Tests for export format selection and output rendering helpers."""

from pathlib import Path
from types import SimpleNamespace

import src.export_formats as mod
from src.Generate_AI_Resume import ResumeItem, OOPPrinciple

def _sample_resume_item() -> ResumeItem:
    """Build a representative ResumeItem fixture for export tests."""
    return ResumeItem(
        project_title="Demo Project",
        one_sentence_summary="Built a demo",
        detailed_summary="Detailed summary here",
        key_responsibilities=["Did the thing"],
        key_skills_used=["Python"],
        tech_stack="Python, FastAPI",
        impact="Improved velocity",
        oop_principles_detected={
            "abstraction": OOPPrinciple(
                present=True,
                description="Uses classes",
                code_snippets=[],
            )
        },
    )

def test_normalize_formats_accepts_pdf_html_md():
    """Accept pdf/html/md tokens regardless of commas or whitespace."""
    assert mod._normalize_formats("pdf, html md") == ["pdf", "html", "md"]

def test_normalize_formats_rejects_invalid():
    """Reject unsupported format tokens."""
    assert mod._normalize_formats("pdf,doc") == []

def test_export_resume_item_writes_html_md(tmp_path):
    """Exporting a full resume item should write html + md outputs."""
    ctx = SimpleNamespace(legacy_save_dir=tmp_path)
    item = _sample_resume_item()

    export_dir, saved = mod.export_resume_item(
        item,
        ctx,
        artifact="portfolio",
        formats=["html", "md"],
        document_title="Portfolio",
    )

    html_path = export_dir / "portfolio.html"
    md_path = export_dir / "portfolio.md"

    assert html_path in saved
    assert md_path in saved
    assert html_path.exists()
    assert md_path.exists()
    assert "Portfolio" in html_path.read_text(encoding="utf-8")
    assert "# Portfolio" in md_path.read_text(encoding="utf-8")

def test_export_resume_line_writes_html_md(tmp_path):
    """Exporting a resume line should write html + md outputs."""
    ctx = SimpleNamespace(legacy_save_dir=tmp_path)
    item = _sample_resume_item()

    export_dir, saved = mod.export_resume_line(
        item,
        ctx,
        artifact="resume",
        formats=["html", "md"],
        document_title="Resume Line",
    )

    html_path = export_dir / "resume.html"
    md_path = export_dir / "resume.md"

    assert html_path in saved
    assert md_path in saved
    assert html_path.exists()
    assert md_path.exists()
    assert "Resume Line" in html_path.read_text(encoding="utf-8")
    assert "# Resume Line" in md_path.read_text(encoding="utf-8")

def test_export_resume_item_pdf_calls_generator(monkeypatch, tmp_path):
    """PDF export should call the generator and optionally create resume line PDF."""
    ctx = SimpleNamespace(legacy_save_dir=tmp_path)
    item = _sample_resume_item()

    calls = {"generate": False, "resume_line": False}

    class FakeGenerator:
        def __init__(self, folderPath, data, fileName):
            self.folder_path = Path(folderPath)
            self.data = data
            self.fileName = fileName
            self.project_title = data.project_title

        def generate(self, name=""):
            calls["generate"] = True

        def create_resume_line(self):
            calls["resume_line"] = True

    import src.resume_pdf_generator as pdf_mod
    monkeypatch.setattr(pdf_mod, "SimpleResumeGenerator", FakeGenerator)

    export_dir, saved = mod.export_resume_item(
        item,
        ctx,
        artifact="portfolio",
        formats=["pdf"],
        document_title="Portfolio",
        include_resume_line_pdf=True,
    )

    assert calls["generate"] is True
    assert calls["resume_line"] is True
    assert export_dir / "portfolio.pdf" in saved
    assert export_dir / f"{item.project_title}_resume_line.pdf" in saved
