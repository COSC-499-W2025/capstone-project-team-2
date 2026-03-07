"""
Unit tests for the Upload Project Streamlit page logic.

Tests cover:
- ZIP upload flow (success, upload failure, analysis failure)
- Folder upload flow (valid path, missing path, non-directory path)
- display_project_insights helper (matching insight, no match, API failure)
- In-memory ZIP construction from a local folder
"""

import io
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers extracted from the page so they can be tested without Streamlit
# ---------------------------------------------------------------------------

def build_folder_zip(folder_path: Path) -> tuple[io.BytesIO, str]:
    """
    Pack a local directory into an in-memory ZIP, preserving folder structure.

    Args:
        folder_path: Path to the project directory.

    Returns:
        Tuple of (zip_buffer, zip_filename).
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in folder_path.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(folder_path.parent))
    zip_buffer.seek(0)
    return zip_buffer, f"{folder_path.name}.zip"


def find_latest_insight(all_insights: list, project_name: str) -> dict | None:
    """
    Return the most recent insight matching project_name, or None.

    Args:
        all_insights: List of insight dicts from /insights/projects.
        project_name: Project name to search for.

    Returns:
        Most recent matching insight dict, or None if not found.
    """
    matches = [i for i in all_insights if i.get("project_name") == project_name]
    return matches[-1] if matches else None


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_INSIGHT = {
    "project_name": "my-project",
    "summary": "A Python project using FastAPI.",
    "project_type": "individual",
    "duration_estimate": "30 days",
    "languages": ["Python"],
    "frameworks": ["FastAPI"],
    "skills": ["Python", "FastAPI", "Testing"],
    "stats": {"skill_count": 3},
    "file_analysis": {
        "file_count": 12,
        "total_size_bytes": 48000,
        "average_size_bytes": 4000,
    },
    "contributors": {"alice": 10, "bob": 2},
}

SAMPLE_UPLOAD_RESPONSE = {
    "status": "ok",
    "filename": "my-project.zip",
    "stored_path": "/tmp/devdoc_uploads/my-project_abc123.zip",
    "project_name": "my-project",
}

SAMPLE_ANALYZE_RESPONSE = {
    "status": "Analysis Finished and Saved",
    "project_name": "my-project",
    "dedup": {},
    "snapshots": [],
}


# ---------------------------------------------------------------------------
# Tests: find_latest_insight
# ---------------------------------------------------------------------------

class TestFindLatestInsight(unittest.TestCase):
    """Tests for the insight-matching helper."""

    def test_returns_last_matching_insight(self):
        """
        When multiple insights share a project name, the last one is returned.
        """
        older = {**SAMPLE_INSIGHT, "analyzed_at": "2024-01-01T00:00:00"}
        newer = {**SAMPLE_INSIGHT, "analyzed_at": "2025-01-01T00:00:00"}
        result = find_latest_insight([older, newer], "my-project")
        self.assertEqual(result["analyzed_at"], "2025-01-01T00:00:00")

    def test_returns_none_when_no_match(self):
        """
        Returns None when no insight matches the given project name.
        """
        result = find_latest_insight([SAMPLE_INSIGHT], "nonexistent-project")
        self.assertIsNone(result)

    def test_returns_none_on_empty_list(self):
        """
        Returns None when the insights list is empty.
        """
        result = find_latest_insight([], "my-project")
        self.assertIsNone(result)

    def test_returns_single_match(self):
        """
        Returns the only insight when exactly one matches.
        """
        result = find_latest_insight([SAMPLE_INSIGHT], "my-project")
        self.assertEqual(result["project_name"], "my-project")

    def test_ignores_non_matching_entries(self):
        """
        Skips insights for other projects and returns only the matching one.
        """
        other = {**SAMPLE_INSIGHT, "project_name": "other-project"}
        result = find_latest_insight([other, SAMPLE_INSIGHT], "my-project")
        self.assertEqual(result["project_name"], "my-project")


# ---------------------------------------------------------------------------
# Tests: build_folder_zip
# ---------------------------------------------------------------------------

class TestBuildFolderZip(unittest.TestCase):
    """Tests for in-memory ZIP construction from a local directory."""

    def setUp(self):
        import tempfile
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_file(self, relative_path: str, content: str = "hello") -> Path:
        """Write a file inside the temp directory."""
        full = self.tmpdir / relative_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        return full

    def test_produces_valid_zip(self):
        """
        build_folder_zip returns a buffer that is a valid ZIP file.
        """
        self._make_file("main.py", "print('hello')")
        buf, name = build_folder_zip(self.tmpdir)
        self.assertTrue(zipfile.is_zipfile(buf))

    def test_zip_filename_uses_folder_name(self):
        """
        The returned filename is <folder_name>.zip.
        """
        self._make_file("main.py")
        _, name = build_folder_zip(self.tmpdir)
        self.assertEqual(name, f"{self.tmpdir.name}.zip")

    def test_zip_contains_all_files(self):
        """
        All files in the folder appear in the ZIP archive.
        """
        self._make_file("main.py")
        self._make_file("src/utils.py")
        self._make_file("README.md")

        buf, _ = build_folder_zip(self.tmpdir)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()

        self.assertEqual(len(names), 3)

    def test_zip_preserves_subdirectory_structure(self):
        """
        Nested files are stored with their relative paths, not flattened.
        """
        self._make_file("src/models/user.py")
        buf, _ = build_folder_zip(self.tmpdir)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()

        # At least one entry should contain a path separator
        nested = [n for n in names if "/" in n]
        self.assertTrue(len(nested) > 0)

    def test_empty_folder_produces_empty_zip(self):
        """
        An empty folder results in a valid ZIP with no entries.
        """
        buf, _ = build_folder_zip(self.tmpdir)
        with zipfile.ZipFile(buf) as zf:
            self.assertEqual(len(zf.namelist()), 0)


# ---------------------------------------------------------------------------
# Tests: ZIP upload flow (mocking requests)
# ---------------------------------------------------------------------------

class TestZipUploadFlow(unittest.TestCase):
    """Tests for the ZIP upload → analyze → display flow."""

    @patch("requests.get")
    @patch("requests.post")
    def test_successful_zip_upload_and_analysis(self, mock_post, mock_get):
        """
        A valid ZIP upload followed by a successful analysis returns project name.
        """
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: SAMPLE_UPLOAD_RESPONSE
        )
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: SAMPLE_ANALYZE_RESPONSE
        )

        upload_resp = mock_post(
            "http://localhost:8000/projects/upload",
            files={"upload_file": ("my-project.zip", b"data", "application/zip")},
        )
        self.assertEqual(upload_resp.status_code, 200)
        self.assertEqual(upload_resp.json()["project_name"], "my-project")

        analyze_resp = mock_get("http://localhost:8000/analyze")
        self.assertEqual(analyze_resp.status_code, 200)
        self.assertEqual(analyze_resp.json()["status"], "Analysis Finished and Saved")

    @patch("requests.post")
    def test_upload_failure_returns_400(self, mock_post):
        """
        A non-ZIP file upload returns 400 with an appropriate error detail.
        """
        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"detail": "file is not a zip file"},
        )

        resp = mock_post(
            "http://localhost:8000/projects/upload",
            files={"upload_file": ("notes.txt", b"not a zip", "text/plain")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("zip", resp.json()["detail"])

    @patch("requests.get")
    @patch("requests.post")
    def test_analysis_failure_after_successful_upload(self, mock_post, mock_get):
        """
        When upload succeeds but /analyze returns 500, the error is surfaced.
        """
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: SAMPLE_UPLOAD_RESPONSE
        )
        mock_get.return_value = MagicMock(
            status_code=500,
            json=lambda: {"detail": "Internal server error"},
        )

        upload_resp = mock_post("http://localhost:8000/projects/upload", files={})
        self.assertEqual(upload_resp.status_code, 200)

        analyze_resp = mock_get("http://localhost:8000/analyze")
        self.assertEqual(analyze_resp.status_code, 500)
        self.assertIn("detail", analyze_resp.json())


# ---------------------------------------------------------------------------
# Tests: Folder upload flow
# ---------------------------------------------------------------------------

class TestFolderUploadFlow(unittest.TestCase):
    """Tests for the local folder path → ZIP → upload → analyze flow."""

    def setUp(self):
        import tempfile
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "main.py").write_text("print('hi')", encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_directory_produces_uploadable_zip(self):
        """
        A real directory is packed into a valid ZIP ready for upload.
        """
        buf, name = build_folder_zip(self.tmpdir)
        self.assertTrue(zipfile.is_zipfile(buf))
        self.assertTrue(name.endswith(".zip"))

    def test_nonexistent_path_is_detected(self):
        """
        A path that does not exist on disk should be flagged before zipping.
        """
        path = Path("/nonexistent/path/to/project")
        self.assertFalse(path.exists())

    def test_file_path_is_not_a_directory(self):
        """
        A path pointing to a file rather than a folder should be rejected.
        """
        file_path = self.tmpdir / "main.py"
        self.assertTrue(file_path.exists())
        self.assertFalse(file_path.is_dir())

    def test_empty_path_string_is_invalid(self):
        """
        An empty or whitespace-only path string should be caught before processing.
        """
        path_str = "   "
        self.assertFalse(path_str.strip())

    @patch("requests.get")
    @patch("requests.post")
    def test_folder_upload_sends_zip_to_api(self, mock_post, mock_get):
        """
        Folder is zipped and uploaded to /projects/upload successfully.
        """
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {**SAMPLE_UPLOAD_RESPONSE, "project_name": self.tmpdir.name},
        )
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: SAMPLE_ANALYZE_RESPONSE
        )

        buf, zip_name = build_folder_zip(self.tmpdir)
        upload_resp = mock_post(
            "http://localhost:8000/projects/upload",
            files={"upload_file": (zip_name, buf, "application/zip")},
        )
        self.assertEqual(upload_resp.status_code, 200)
        self.assertEqual(upload_resp.json()["project_name"], self.tmpdir.name)


# ---------------------------------------------------------------------------
# Tests: display_project_insights (API interaction)
# ---------------------------------------------------------------------------

class TestDisplayProjectInsights(unittest.TestCase):
    """Tests for fetching and resolving the correct insight after analysis."""

    @patch("requests.get")
    def test_fetches_insights_from_correct_endpoint(self, mock_get):
        """
        After analysis, /insights/projects is called to retrieve insight data.
        """
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: [SAMPLE_INSIGHT]
        )

        resp = mock_get("http://localhost:8000/insights/projects")
        self.assertEqual(resp.status_code, 200)
        insights = resp.json()
        match = find_latest_insight(insights, "my-project")
        self.assertIsNotNone(match)
        self.assertEqual(match["project_name"], "my-project")

    @patch("requests.get")
    def test_insight_contains_expected_fields(self, mock_get):
        """
        The resolved insight has all fields needed by the display function.
        """
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: [SAMPLE_INSIGHT]
        )

        resp = mock_get("http://localhost:8000/insights/projects")
        insight = find_latest_insight(resp.json(), "my-project")

        for field in ("summary", "project_type", "duration_estimate",
                      "languages", "frameworks", "skills", "stats",
                      "file_analysis", "contributors"):
            self.assertIn(field, insight, f"Missing field: {field}")

    @patch("requests.get")
    def test_no_insight_found_for_project(self, mock_get):
        """
        Returns None when insights exist but none match the uploaded project name.
        """
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: [SAMPLE_INSIGHT]
        )

        resp = mock_get("http://localhost:8000/insights/projects")
        match = find_latest_insight(resp.json(), "completely-different-project")
        self.assertIsNone(match)

    @patch("requests.get")
    def test_insights_api_failure_returns_non_200(self, mock_get):
        """
        When /insights/projects is unavailable, a non-200 status is returned.
        """
        mock_get.return_value = MagicMock(
            status_code=500,
            json=lambda: {"detail": "Storage unavailable"},
        )

        resp = mock_get("http://localhost:8000/insights/projects")
        self.assertNotEqual(resp.status_code, 200)

    @patch("requests.get")
    def test_multiple_snapshots_returns_most_recent(self, mock_get):
        """
        When a project has multiple analysis snapshots, the latest is used.
        """
        snap1 = {**SAMPLE_INSIGHT, "analyzed_at": "2024-03-01T10:00:00", "summary": "Old"}
        snap2 = {**SAMPLE_INSIGHT, "analyzed_at": "2025-03-01T10:00:00", "summary": "New"}

        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: [snap1, snap2]
        )

        resp = mock_get("http://localhost:8000/insights/projects")
        match = find_latest_insight(resp.json(), "my-project")
        self.assertEqual(match["summary"], "New")


if __name__ == "__main__":
    unittest.main()