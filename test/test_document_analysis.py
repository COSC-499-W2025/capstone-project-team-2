from pathlib import Path

import pytest

from src.core.document_analysis import DocumentAnalyzer


def test_text_metrics_dates_roles_and_skills(tmp_path: Path) -> None:
    """
    TXT content should surface metrics, dates, roles, and skills.
    """
    note = tmp_path / "note.txt"
    note.write_text(
        "Lead engineer improved uptime by 25% in Jan 2023-2024 using Python and Docker."
    )

    result = DocumentAnalyzer(tmp_path).analyze()
    doc = result["documents"][0]

    assert doc["format"] == "TXT"
    assert "25%" in doc["metrics"]
    assert any("2023" in d for d in doc["dates"])
    assert "Engineer" in doc["roles"]
    assert "Python" in doc["skills"]
    assert result["summary"]["unique_documents"] == 1


def test_markdown_research_doc_type_and_summary(tmp_path: Path) -> None:
    """
    Markdown with research-style sections should classify as research paper
    and produce a summary and key points.
    """
    md = tmp_path / "paper.md"
    md.write_text(
        "# Abstract\nWe present a lightweight method for local artifact mining that extracts text signals and metadata to summarize outcomes for portfolios.\n\n"
        "# Introduction\nThis approach reduces manual portfolio effort while keeping analysis privacy-preserving and local.\n\n"
        "# Conclusion\nOur approach keeps data local, accelerates résumé preparation, and improves discovery of meaningful work artifacts.\n"
    )

    result = DocumentAnalyzer(tmp_path).analyze()
    doc = result["documents"][0]

    assert doc["format"] == "MD"
    assert doc["doc_type"]["label"] == "research paper"
    assert doc["summary"]
    assert doc["key_points"]
    assert result["summary"]["by_format"].get("MD") == 1


def test_duplicate_detection_by_hash(tmp_path: Path) -> None:
    """
    Duplicate files with identical content should be reported once with a duplicate entry.
    """
    content = "Same content for both files."
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text(content)
    b.write_text(content)

    result = DocumentAnalyzer(tmp_path).analyze()

    assert len(result["documents"]) == 1
    assert len(result["duplicates"]) == 1
    dup_path = result["duplicates"][0]["path"]
    assert dup_path in {"a.txt", "b.txt"}


def test_unreadable_file_goes_to_errors(tmp_path: Path, monkeypatch) -> None:
    """
    Unreadable files should not crash analysis; they should be reported in errors.
    """
    bad = tmp_path / "bad.txt"
    bad.write_text("content")

    def boom(path):
        raise IOError("boom")

    monkeypatch.setattr("src.core.document_analysis.compute_sha256", boom)

    result = DocumentAnalyzer(tmp_path).analyze()

    assert result["documents"] == []
    assert result["duplicates"] == []
    assert result["summary"]["unique_documents"] == 0
    assert any("boom" in e for e in result["errors"])
