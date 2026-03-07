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


class TestAddProjectManual(_BaseResumeTest):
    """Tests for POST /resume/{id}/add/project/manual."""

    def test_success_all_fields(self):
        """All fields provided returns 200 with success status."""
        self.mock_doc.add_project.return_value = "Successfully added project 'My Side Project'"
        resp = self.client.post("/resume/test_abc123/add/project/manual", json={
            "name": "My Side Project",
            "start_date": "2024-01",
            "end_date": "2025-03",
            "location": "Vancouver, BC",
            "summary": "A personal project to explore Rust.",
            "highlights": ["Built async runtime", "Achieved 10k RPS"],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])
        self.mock_doc.add_project.assert_called_once()

    def test_success_name_only(self):
        """Only required `name` field; all optional fields default to None."""
        self.mock_doc.add_project.return_value = "Successfully added project 'Minimal'"
        resp = self.client.post("/resume/test_abc123/add/project/manual", json={"name": "Minimal"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

    def test_missing_name_returns_422(self):
        """Request without required `name` field returns 422 validation error."""
        resp = self.client.post("/resume/test_abc123/add/project/manual", json={
            "summary": "No name provided",
        })
        self.assertEqual(resp.status_code, 422)

    def test_check_result_failure_returns_400(self):
        """Non-success result string from add_project returns 400."""
        self.mock_doc.add_project.return_value = "Failed: duplicate project name"
        resp = self.client.post("/resume/test_abc123/add/project/manual", json={"name": "Duplicate"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("duplicate project name", resp.json()["detail"])

    def test_unexpected_error_returns_500(self):
        """RuntimeError during add_project returns 500."""
        self.mock_doc.add_project.side_effect = RuntimeError("disk full")
        resp = self.client.post("/resume/test_abc123/add/project/manual", json={"name": "My Project"})
        self.assertEqual(resp.status_code, 500)
        self.assertIn("disk full", resp.json()["detail"])

    def test_resume_not_found_returns_404(self):
        """Missing resume returns 404."""
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/add/project/manual", json={"name": "My Project"})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])


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

    def test_add_connection(self):
        """Adding a new connection via edit calls add_connection."""
        self.mock_doc.get_connections.return_value = []
        self.mock_doc.add_connection.return_value = "Successfully added: GitHub"

        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "connections", "item_name": "GitHub", "field": "username", "new_value": "jdoe"}]
        })
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.add_connection.assert_called_once()

    def test_modify_connection(self):
        """Modifying an existing connection via edit calls modify_connection."""
        self.mock_doc.get_connections.return_value = [{"network": "GitHub", "username": "old"}]
        self.mock_doc.modify_connection.return_value = "Successfully updated: GitHub"

        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "connections", "item_name": "GitHub", "field": "username", "new_value": "newuser"}]
        })
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.modify_connection.assert_called_once_with("GitHub", "newuser")

    def test_remove_connection(self):
        """Removing a connection via edit with field='delete' calls remove_connection."""
        self.mock_doc.remove_connection.return_value = "Successfully deleted: GitHub"

        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "connections", "item_name": "GitHub", "field": "delete", "new_value": ""}]
        })
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.remove_connection.assert_called_once_with("GitHub")

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


class TestGenerateAndEditEdgeCases(_BaseResumeTest):
    """Edge cases for generate and edit endpoints."""

    def test_generate_invalid_theme_and_default_skips_update(self):
        """Invalid theme returns 400; default theme 'sb2nov' skips update_theme."""
        # Invalid theme
        self.mock_doc.generate.return_value = "Generated"
        self.mock_doc.update_theme.side_effect = ValueError("Invalid theme 'bad'. Available: classic, sb2nov")
        resp = self.client.post("/resume/generate", json={"name": "John", "theme": "bad"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid theme", resp.json()["detail"])

        # Default theme skips update
        self.mock_doc.update_theme.side_effect = None
        self.mock_doc.update_theme.reset_mock()
        resp = self.client.post("/resume/generate", json={"name": "John", "theme": "sb2nov"})
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.update_theme.assert_not_called()

    def test_edit_invalid_contact_field_and_theme_and_check_result(self):
        """Invalid contact field, invalid theme in edit, and _check_result failure all return 400."""
        # Invalid contact field
        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "contact", "item_name": "", "field": "fax", "new_value": "555-0000"}]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unknown contact field", resp.json()["detail"])

        # Invalid theme in edit
        self.mock_doc.update_theme.side_effect = ValueError("Invalid theme 'nope'")
        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "theme", "item_name": "", "field": "", "new_value": "nope"}]
        })
        self.assertEqual(resp.status_code, 400)

        # _check_result failure
        self.mock_doc.update_theme.side_effect = None
        self.mock_doc.update_summary.return_value = "Failed to update summary"
        resp = self.client.post("/resume/test_abc123/edit", json={
            "edits": [{"section": "summary", "item_name": "", "field": "", "new_value": "text"}]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Failed to update summary", resp.json()["detail"])

    @patch("src.API.Resume_Generator_API.shutil")
    def test_default_render_returns_pdf(self, _mock_shutil):
        """POST /resume/{id}/render (no format) defaults to PDF."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_pdf = Path(tmp_dir) / "resume.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            self.mock_doc.render_outputs.return_value = (
                "successfully rendered",
                {"pdf": [fake_pdf]},
            )
            resp = self.client.post("/resume/test_abc123/render")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers["content-type"], "application/pdf")
            self.assertIn("X-Resume-ID", resp.headers)

    def test_delete_os_error_returns_500(self):
        """OSError during resume deletion returns 500."""
        self.mock_doc.yaml_file = MagicMock()
        self.mock_doc.yaml_file.unlink.side_effect = OSError("Permission denied")
        resp = self.client.delete("/resume/test_abc123")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Permission denied", resp.json()["detail"])


class TestRemoveProject(_BaseResumeTest):
    """Tests for DELETE /resume/{id}/project/{project_name}."""

    def test_success_and_error_cases(self):
        """Covers success, project not found, no projects, and resume not found."""
        # Success
        self.mock_doc.remove_project.return_value = "Successfully removed project 'MyProject'"
        resp = self.client.delete("/resume/test_abc123/project/MyProject")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # Project not found
        self.mock_doc.remove_project.return_value = "Project 'Unknown' not found"
        resp = self.client.delete("/resume/test_abc123/project/Unknown")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # No projects at all
        self.mock_doc.remove_project.return_value = "No projects in resume"
        resp = self.client.delete("/resume/test_abc123/project/SomeProject")
        self.assertEqual(resp.status_code, 404)

        # Resume itself not found
        self._set_not_found()
        resp = self.client.delete("/resume/fake_id/project/MyProject")
        self.assertEqual(resp.status_code, 404)


class TestEducationEndpoints(_BaseResumeTest):
    """Tests for POST /resume/{id}/add/education and DELETE /resume/{id}/education/{name}."""

    def test_add_and_remove_education(self):
        """Covers add success, duplicate (409), bad result (400), remove success, and remove not found (404)."""
        # Add success
        self.mock_doc.add_education.return_value = "Successfully added education"
        resp = self.client.post("/resume/test_abc123/add/education", json={
            "institution": "University of British Columbia",
            "area": "Computer Science",
            "degree": "BSc",
            "start_date": "2021-09",
            "end_date": "2025-04",
            "location": "Kelowna, BC",
            "gpa": "3.8",
            "highlights": ["Dean's List"],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "Successfully added education")

        # Duplicate returns 409
        self.mock_doc.add_education.return_value = "Duplicate institution 'UBC' already exists"
        resp = self.client.post("/resume/test_abc123/add/education", json={
            "institution": "UBC", "area": "CS",
        })
        self.assertEqual(resp.status_code, 409)
        self.assertIn("Duplicate", resp.json()["detail"])

        # Bad result returns 400
        self.mock_doc.add_education.return_value = "Invalid education entry"
        resp = self.client.post("/resume/test_abc123/add/education", json={
            "institution": "UBC", "area": "CS",
        })
        self.assertEqual(resp.status_code, 400)

        # Remove success
        self.mock_doc.remove_education.return_value = "Successfully removed education 'UBC'"
        resp = self.client.delete("/resume/test_abc123/education/UBC")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # Remove not found
        self.mock_doc.remove_education.return_value = "Institution 'Unknown' not found"
        resp = self.client.delete("/resume/test_abc123/education/Unknown")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # Remove when education list is empty
        self.mock_doc.remove_education.return_value = "No education to delete"
        resp = self.client.delete("/resume/test_abc123/education/UBC")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("No education to delete", resp.json()["detail"])

    def test_resume_not_found(self):
        """Both add and remove return 404 for missing resume."""
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/add/education", json={
            "institution": "UBC", "area": "CS",
        })
        self.assertEqual(resp.status_code, 404)

        resp = self.client.delete("/resume/fake_id/education/UBC")
        self.assertEqual(resp.status_code, 404)


class TestExperienceEndpoints(_BaseResumeTest):
    """Tests for POST /resume/{id}/add/experience and DELETE /resume/{id}/experience/{name}."""

    def test_add_and_remove_experience(self):
        """Covers add success, add failure (400), remove success, and remove not found (404)."""
        # Add success
        self.mock_doc.add_experience.return_value = "Successfully added experience"
        resp = self.client.post("/resume/test_abc123/add/experience", json={
            "company": "Acme Corp",
            "position": "Software Engineer",
            "start_date": "2023-05",
            "end_date": "present",
            "location": "Vancouver, BC",
            "highlights": ["Built REST APIs"],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "Successfully added experience")

        # Add failure
        self.mock_doc.add_experience.return_value = "Company name cannot be empty"
        resp = self.client.post("/resume/test_abc123/add/experience", json={
            "company": "", "position": "Dev",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Company name", resp.json()["detail"])

        # Remove success
        self.mock_doc.remove_experience.return_value = "Successfully removed experience 'Acme Corp'"
        resp = self.client.delete("/resume/test_abc123/experience/Acme%20Corp")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # Remove not found
        self.mock_doc.remove_experience.return_value = "Company 'Unknown' not found"
        resp = self.client.delete("/resume/test_abc123/experience/Unknown")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # Remove when experience list is empty
        self.mock_doc.remove_experience.return_value = "No experience to delete"
        resp = self.client.delete("/resume/test_abc123/experience/Acme%20Corp")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("No experience to delete", resp.json()["detail"])

    def test_resume_not_found(self):
        """Both add and remove return 404 for missing resume."""
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/add/experience", json={
            "company": "Acme Corp",
        })
        self.assertEqual(resp.status_code, 404)

        resp = self.client.delete("/resume/fake_id/experience/Acme")
        self.assertEqual(resp.status_code, 404)


class TestAddProjectExtended(_BaseResumeTest):
    """Tests for add-project overrides, _check_result failure, and export not-found."""

    def setUp(self):
        super().setUp()
        patcher = patch(CTX_PATCH)
        self.mock_ctx = patcher.start()
        self.addCleanup(patcher.stop)

    def test_payload_overrides_and_check_result_failure(self):
        """Covers payload overrides succeeding and _check_result rejecting a bad result."""
        # Payload overrides DB values
        self.mock_doc.add_project.return_value = "Successfully added project 'CustomName'"
        self.mock_ctx.store.fetch_by_name.return_value = SAMPLE_DB_RECORD
        resp = self.client.post(
            "/resume/test_abc123/add/project/WarframeFinderStreamlit",
            json={
                "name": "CustomName",
                "start_date": "2024-01",
                "end_date": "2025-06",
                "location": "Vancouver, BC",
                "summary": "Custom summary",
                "highlights": ["Custom highlight"],
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # _check_result rejects non-success string
        self.mock_doc.add_project.return_value = "Failed: duplicate project"
        resp = self.client.post("/resume/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("duplicate project", resp.json()["detail"])


class TestExportResumeErrors(_BaseResumeTest):
    """Test export endpoints return 404 for missing resumes."""

    def test_export_not_found_cases(self):
        """Both default and custom export return 404 for missing resumes."""
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/export/pdf")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        resp = self.client.post("/resume/fake_id/export/pdf/custom", json={"path": "/tmp"})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])


class TestExportResume(_BaseResumeTest):
    """Tests for POST /resume/{id}/export/{format} and /resume/{id}/export/{format}/custom."""

    @patch("src.API.Resume_Generator_API.shutil")
    @patch("src.API.Resume_Generator_API.RENDERED_OUTPUTS_DIR")
    def test_save_default(self, mock_dir, mock_shutil):
        """Save to default directory returns path."""
        mock_dir.mkdir = MagicMock()
        mock_dir.__truediv__ = lambda self, name: Path("/fake/rendered_outputs") / name

        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_pdf = Path(tmp_dir) / "resume.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            self.mock_doc.render_outputs.return_value = ("successfully rendered", {"pdf": [fake_pdf]})

            resp = self.client.post("/resume/test_abc123/export/pdf")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Saved successfully", resp.json()["status"])
            self.assertIn("path", resp.json())

    @patch("src.API.Resume_Generator_API.shutil")
    def test_save_custom(self, mock_shutil):
        """Save to custom directory returns path."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as custom_dir:
            fake_pdf = Path(tmp_dir) / "resume.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            self.mock_doc.render_outputs.return_value = ("successfully rendered", {"pdf": [fake_pdf]})

            resp = self.client.post("/resume/test_abc123/export/pdf/custom", json={"path": custom_dir})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Saved successfully", resp.json()["status"])
            self.assertIn(custom_dir.replace("\\", "/"), resp.json()["path"].replace("\\", "/"))

    def test_save_custom_invalid_dir(self):
        """Save to non-existent directory returns 400."""
        resp = self.client.post("/resume/test_abc123/export/pdf/custom", json={"path": "/nonexistent/dir"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("does not exist", resp.json()["detail"])

    def test_save_unsupported_format(self):
        """Save with unsupported format returns 400."""
        resp = self.client.post("/resume/test_abc123/export/docx")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported format", resp.json()["detail"])


class TestSkillEndpoints(_BaseResumeTest):
    """Tests for POST /resume/{id}/add/skill, POST /resume/{id}/skill/{label}/append, DELETE /resume/{id}/skill/{label}."""

    def test_add_skill(self):
        """Covers success, duplicate (409), failure (400), and resume not found (404)."""
        # Success
        self.mock_doc.add_skills.return_value = "Successfully added skills"
        resp = self.client.post("/resume/test_abc123/add/skill", json={
            "label": "Languages",
            "details": "Python, Java, C++",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "Successfully added skills")

        # Duplicate label returns 409
        self.mock_doc.add_skills.return_value = "Duplicate label 'Languages' already exists"
        resp = self.client.post("/resume/test_abc123/add/skill", json={
            "label": "Languages",
            "details": "Python",
        })
        self.assertEqual(resp.status_code, 409)
        self.assertIn("Duplicate", resp.json()["detail"])

        # Generic failure returns 400
        self.mock_doc.add_skills.return_value = "Label cannot be empty"
        resp = self.client.post("/resume/test_abc123/add/skill", json={
            "label": "Languages",
            "details": "Python",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Label cannot be empty", resp.json()["detail"])

        # Resume not found
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/add/skill", json={
            "label": "Languages",
            "details": "Python",
        })
        self.assertEqual(resp.status_code, 404)

    def test_append_skill(self):
        """Covers append success (merges details), skill not found (404), and resume not found (404)."""
        # Success — appends to existing details
        self.mock_doc.get_skills.return_value = [
            {"label": "Languages", "details": "Python, Java"}
        ]
        self.mock_doc.modify_skill.return_value = "Successfully modified skill"
        resp = self.client.post("/resume/test_abc123/skill/Languages/append", json={
            "details": "C++",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["details"], "Python, Java, C++")
        self.assertIn("Successfully", resp.json()["status"])
        self.mock_doc.modify_skill.assert_called_once_with("Languages", "Python, Java, C++")

        # Skill label not found returns 404
        self.mock_doc.get_skills.return_value = []
        resp = self.client.post("/resume/test_abc123/skill/Unknown/append", json={
            "details": "Rust",
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # Resume not found
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/skill/Languages/append", json={
            "details": "Rust",
        })
        self.assertEqual(resp.status_code, 404)

    def test_remove_skill(self):
        """Covers remove success, label not found (404), no skills (404), and resume not found (404)."""
        # Success
        self.mock_doc.remove_skill.return_value = "Successfully removed skill 'Languages'"
        resp = self.client.delete("/resume/test_abc123/skill/Languages")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # Label not found returns 404
        self.mock_doc.remove_skill.return_value = "Skill 'Unknown' not found"
        resp = self.client.delete("/resume/test_abc123/skill/Unknown")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # No skills on the resume returns 404
        self.mock_doc.remove_skill.return_value = "No skills in resume"
        resp = self.client.delete("/resume/test_abc123/skill/Languages")
        self.assertEqual(resp.status_code, 404)

        # Resume not found
        self._set_not_found()
        resp = self.client.delete("/resume/fake_id/skill/Languages")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
