"""
Unit tests for Resume_Generator_API.py

Uses FastAPI's TestClient to simulate HTTP calls without running a real server.
All external dependencies (RenderCVDocument, runtimeAppContext) are mocked.
"""

import unittest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient

from src.API.general_API import app

DOC_PATCH = "src.API.Resume_Generator_API.RenderCVDocument"
CTX_PATCH = "src.API.Resume_Generator_API.runtimeAppContext"

SAMPLE_DB_RECORD = {
    "hierarchy": {"name": "WarframeFinderStreamlit", "type": "DIR", "children": []},
    "resume_item": {
        "project_name": "WarframeFinderStreamlit",
        "summary": "Built WarframeFinderStreamlit with Python; framework Streamlit, leveraging Git-backed collaboration.",
        "highlights": [
            "Implemented core functionality using Python; framework Streamlit.",
            "Demonstrated skills: Data Analysis, Data Visualization, Python, and Streamlit.",
            "Managed version control workflows in Git."
        ],
        "project_type": "individual",
        "detection_mode": "git",
        "languages": ["Python"],
        "frameworks": ["Streamlit"],
        "skills": ["Data Analysis", "Data Visualization", "Python", "Streamlit"],
        "framework_sources": {"Streamlit": ["requirements.txt"]}
    },
    "project_root": "D:\\Python Project\\WarframeFinderStreamlit",
    "project_type": {"mode": "git", "project_type": "individual"},
    "duration_estimate": "754 days, 13:17:35.854911"
}


class _BaseResumeTest(unittest.TestCase):
    """Shared setup: patches RenderCVDocument and creates a TestClient."""

    def setUp(self):
        self.client = TestClient(app)
        patcher = patch(DOC_PATCH)
        self.mock_doc_cls = patcher.start()
        self.mock_doc = MagicMock()
        self.mock_doc_cls.return_value = self.mock_doc
        self.addCleanup(patcher.stop)

    def _set_not_found(self):
        """Configure mock so _load_resume raises 404."""
        self.mock_doc.load.side_effect = FileNotFoundError


class TestResumeFullWorkflow(_BaseResumeTest):
    """End-to-end test covering generate -> get -> edit -> render -> delete."""

    @patch("src.API.Resume_Generator_API.shutil")
    def test_full_lifecycle(self, _mock_shutil):
        """Exercises every endpoint in the typical user workflow."""
        # 1. Generate resume
        self.mock_doc.generate.return_value = "Generated"
        resp = self.client.post("/resume/generate", json={"name": "John"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("resume_id", data)
        self.assertEqual(data["status"], "Resume created successfully")
        self.assertTrue(data["resume_id"].startswith("John_"))
        resume_id = data["resume_id"]

        # 2. Get resume — verify all expected sections are present
        resp = self.client.get(f"/resume/{resume_id}")
        self.assertEqual(resp.status_code, 200)
        for key in ["name", "contact", "theme", "summary", "experience",
                     "education", "projects", "skills", "connections"]:
            self.assertIn(key, resp.json())

        # 3. Edit resume — batch edit across all section types
        self.mock_doc.modify_experience.return_value = "Successfully modified position"
        self.mock_doc.modify_education.return_value = "Successfully modified area"
        self.mock_doc.modify_project.return_value = "Successfully modified project"
        self.mock_doc.modify_skill.return_value = "Successfully modified skill"
        self.mock_doc.update_summary.return_value = "Successfully updated summary"
        self.mock_doc.update_theme.return_value = "Successfully updated theme"

        resp = self.client.post(f"/resume/{resume_id}/edit", json={"edits": [
            {"section": "experience", "item_name": "Google", "field": "position", "new_value": "Lead"},
            {"section": "education", "item_name": "UBC", "field": "area", "new_value": "CS"},
            {"section": "projects", "item_name": "App", "field": "summary", "new_value": "New summary"},
            {"section": "skills", "item_name": "Python", "field": "", "new_value": "Python 3.12"},
            {"section": "summary", "item_name": "", "field": "", "new_value": "New text"},
            {"section": "contact", "item_name": "", "field": "email", "new_value": "a@b.com"},
            {"section": "theme", "item_name": "", "field": "", "new_value": "classic"},
        ]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 7)

        # 4. Render resume in all supported formats
        format_cases = [
            ("pdf", "resume.pdf", b"%PDF-1.4 fake", "application/pdf"),
            ("html", "resume.html", b"<html>test</html>", "text/html; charset=utf-8"),
            ("markdown", "resume.md", b"# Resume", "text/markdown; charset=utf-8"),
        ]
        for fmt, filename, content, expected_type in format_cases:
            with self.subTest(format=fmt), tempfile.TemporaryDirectory() as tmp_dir:
                fake_file = Path(tmp_dir) / filename
                fake_file.write_bytes(content)
                self.mock_doc.render_outputs.return_value = (
                    "successfully rendered",
                    {fmt: [fake_file]},
                )

                resp = self.client.post(f"/resume/{resume_id}/render/{fmt}")
                self.assertEqual(resp.status_code, 200)
                self.assertIn("X-Resume-ID", resp.headers)
                self.assertEqual(resp.headers["content-type"], expected_type)

        # 5. Delete resume
        self.mock_doc.yaml_file = MagicMock()
        resp = self.client.delete(f"/resume/{resume_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resume_id, resp.json()["status"])


class TestAddProjectFromDB(_BaseResumeTest):
    """Tests for POST /resume/{id}/add/project/{project_name}."""

    def setUp(self):
        super().setUp()
        patcher = patch(CTX_PATCH)
        self.mock_ctx = patcher.start()
        self.addCleanup(patcher.stop)

    def test_success_and_error_cases(self):
        """Covers successful add, missing DB record, missing resume_item, and unexpected error."""
        # Success — project added from DB
        self.mock_doc.add_project.return_value = "Successfully added project 'WarframeFinderStreamlit'"
        self.mock_ctx.store.fetch_by_name.return_value = SAMPLE_DB_RECORD
        resp = self.client.post("/resume/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # 404 — DB record not found
        self.mock_ctx.store.fetch_by_name.return_value = None
        resp = self.client.post("/resume/test_abc123/add/project/UnknownProject")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found in database", resp.json()["detail"])

        # 400 — record exists but has no resume_item
        self.mock_ctx.store.fetch_by_name.return_value = {"hierarchy": {}, "project_root": "C:\\some\\path"}
        resp = self.client.post("/resume/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("no resume_item", resp.json()["detail"])

        # 500 — unexpected error during save
        self.mock_doc.add_project.side_effect = RuntimeError("disk full")
        self.mock_ctx.store.fetch_by_name.return_value = SAMPLE_DB_RECORD
        resp = self.client.post("/resume/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("disk full", resp.json()["detail"])


class TestErrorHandling(_BaseResumeTest):
    """Consolidated error/edge-case tests across all endpoints."""

    def test_not_found_across_endpoints(self):
        """All endpoints that load an existing resume return 404 for missing IDs."""
        self._set_not_found()

        resp = self.client.get("/resume/fake_id")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        resp = self.client.post("/resume/fake_id/edit", json={
            "edits": [{"section": "summary", "item_name": "", "field": "", "new_value": "text"}]
        })
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post("/resume/fake_id/render/pdf")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.delete("/resume/fake_id")
        self.assertEqual(resp.status_code, 404)

    def test_generate_conflict(self):
        """Generating a resume that already exists returns 409."""
        self.mock_doc.generate.return_value = "Skipping generation"
        resp = self.client.post("/resume/generate", json={"name": "John"})
        self.assertEqual(resp.status_code, 409)
        self.assertIn("already exists", resp.json()["detail"])

    def test_edit_unknown_section(self):
        """Editing an invalid section returns 400."""
        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "invalid", "item_name": "x", "field": "y", "new_value": "z"}]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unknown section", resp.json()["detail"])

    def test_render_failure(self):
        """Render returning empty paths returns 500."""
        self.mock_doc.render_outputs.return_value = ("Render failed", {"pdf": []})
        resp = self.client.post("/resume/test_abc123/render/pdf")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Render failed", resp.json()["detail"])

    def test_render_unsupported_format(self):
        """Render with unsupported format returns 400."""
        resp = self.client.post("/resume/test_abc123/render/docx")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported format", resp.json()["detail"])

    @patch("src.API.Resume_Generator_API.shutil")
    def test_render_output_parent_directory_cleanup(self, _mock_shutil):
        """Verify cleanup targets the parent directory of the rendered file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "rendercv_output"
            output_dir.mkdir()
            fake_pdf = output_dir / "resume.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake content")

            self.mock_doc.render_outputs.return_value = (
                "successfully rendered",
                {"pdf": [fake_pdf]},
            )

            resp = self.client.post("/resume/test_abc123/render/pdf")
            self.assertEqual(resp.status_code, 200)

            # Verify shutil.rmtree was scheduled on the parent dir (output_dir)
            _mock_shutil.rmtree.assert_called_once_with(output_dir, True)


if __name__ == "__main__":
    unittest.main()
