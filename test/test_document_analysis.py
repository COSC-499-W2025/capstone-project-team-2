from src.core.document_analysis import DocumentAnalyzer


def test_document_analysis_signals_and_dedupe(tmp_path):
    """
    Validate parsing signals and duplicate detection in one pass.

    Args:
        tmp_path: Temporary directory fixture.

    Returns:
        None: Assertions validate parsed output.
    """
    note = tmp_path / "note.txt"
    note.write_text("Lead engineer improved uptime by 25% Jan 2023-2024 using Python.")

    first = DocumentAnalyzer(tmp_path).analyze()
    doc = first["documents"][0]

    assert doc["format"] == "TXT"
    assert doc["word_count"] > 0
    assert "25%" in doc["metrics"]
    assert any("2023" in d for d in doc["dates"])
    assert "Engineer" in doc["roles"]
    assert "Python" in doc["skills"]

    second = DocumentAnalyzer(tmp_path, known_hashes=first["hash_index"]).analyze()
    assert second["summary"]["unique_documents"] == 0
    assert second["summary"]["duplicate_documents"] == 1
    assert second["duplicates"][0]["path"] == "note.txt"


def test_markdown_headings_and_summary(tmp_path):
    """
    Ensure markdown parsing captures headings and counts by format.

    Args:
        tmp_path: Temporary directory fixture.

    Returns:
        None: Assertions validate heading detection and summary stats.
    """
    doc = tmp_path / "project.md"
    doc.write_text("# Title\n\n## Subhead\nContent goes here with Docker.")

    result = DocumentAnalyzer(tmp_path).analyze()
    doc_entry = result["documents"][0]

    assert "Title" in doc_entry["headings"]
    assert "Subhead" in doc_entry["headings"]
    assert "Docker" in doc_entry["skills"]
    assert result["summary"]["by_format"].get("MD") == 1


def test_missing_root_returns_error(tmp_path):
    """
    Verify missing roots produce an error entry without raising.

    Args:
        tmp_path: Temporary directory fixture.

    Returns:
        None: Assertions validate the error structure.
    """
    missing = tmp_path / "nope"
    result = DocumentAnalyzer(missing).analyze()

    assert result["documents"] == []
    assert result["summary"]["unique_documents"] == 0
    assert result["errors"]
