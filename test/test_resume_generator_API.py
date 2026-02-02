"""
Unit tests for Resume_Generator_API.py

Uses FastAPI's TestClient to simulate HTTP calls without running a real server.
All external dependencies (RenderCVDocument, runtimeAppContext) are mocked.
"""

import unittest
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


class TestGenerateResume(_BaseResumeTest):
    """Tests for POST /resume/generate."""

    @patch("src.API.Resume_Generator_API.shutil")
    def test_success(self, _mock_shutil):
        self.mock_doc.generate.return_value = "Generated"
        fake_pdf = Path("/tmp/fake_output/resume.pdf")
        fake_pdf.parent.mkdir(parents=True, exist_ok=True)
        fake_pdf.write_bytes(b"%PDF-1.4 fake content")
        self.mock_doc.render.return_value = ("Success", fake_pdf)

        response = self.client.post("/resume/generate", json={"name": "John"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Resume-ID", response.headers)
        self.assertEqual(response.headers["content-type"], "application/pdf")

    def test_already_exists_returns_409(self):
        self.mock_doc.generate.return_value = "Skipping generation"

        response = self.client.post("/resume/generate", json={"name": "John"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("already exists", response.json()["detail"])

    def test_render_failure_returns_500(self):
        self.mock_doc.generate.return_value = "Generated"
        self.mock_doc.render.return_value = ("Render failed", None)

        response = self.client.post("/resume/generate", json={"name": "John"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("Render failed", response.json()["detail"])


class TestGetResume(_BaseResumeTest):
    """Tests for GET /resume/{id}."""

    def test_success(self):
        response = self.client.get("/resume/test_abc123")
        self.assertEqual(response.status_code, 200)
        for key in ["name", "contact", "theme", "summary", "experience",
                     "education", "projects", "skills", "connections"]:
            self.assertIn(key, response.json())

    def test_not_found_returns_404(self):
        self._set_not_found()
        response = self.client.get("/resume/fake_id")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])


class TestEditResume(_BaseResumeTest):
    """Tests for POST /resume/{id}/edit."""

    def _post_edit(self, edits):
        return self.client.post("/resume/test_abc123/edit", json={"edits": edits})

    def test_edit_experience(self):
        self.mock_doc.modify_experience.return_value = "Successfully modified position"
        resp = self._post_edit([{"section": "experience", "item_name": "Google", "field": "position", "new_value": "Senior Dev"}])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully modified position", resp.json()["results"])

    def test_edit_education(self):
        self.mock_doc.modify_education.return_value = "Successfully modified area"
        resp = self._post_edit([{"section": "education", "item_name": "UBC", "field": "area", "new_value": "CS"}])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully modified area", resp.json()["results"])

    def test_edit_skills(self):
        self.mock_doc.modify_skill.return_value = "Successfully modified skill"
        resp = self._post_edit([{"section": "skills", "item_name": "Python", "field": "", "new_value": "Python 3.12"}])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully modified skill", resp.json()["results"])

    def test_edit_summary(self):
        self.mock_doc.update_summary.return_value = "Successfully updated summary"
        resp = self._post_edit([{"section": "summary", "item_name": "", "field": "", "new_value": "New text"}])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully updated summary", resp.json()["results"])

    def test_edit_contact(self):
        resp = self._post_edit([{"section": "contact", "item_name": "", "field": "email", "new_value": "a@b.com"}])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("email", resp.json()["results"][0])

    def test_edit_theme(self):
        self.mock_doc.update_theme.return_value = "Successfully updated theme"
        resp = self._post_edit([{"section": "theme", "item_name": "", "field": "", "new_value": "classic"}])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully updated theme", resp.json()["results"])

    def test_multiple_edits(self):
        self.mock_doc.modify_experience.return_value = "ok"
        self.mock_doc.modify_education.return_value = "ok"
        self.mock_doc.modify_skill.return_value = "ok"
        resp = self._post_edit([
            {"section": "experience", "item_name": "Google", "field": "position", "new_value": "Lead"},
            {"section": "education", "item_name": "UBC", "field": "area", "new_value": "CS"},
            {"section": "skills", "item_name": "Python", "field": "", "new_value": "Python 3.12"},
        ])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 3)

    def test_unknown_section_returns_400(self):
        resp = self._post_edit([{"section": "invalid", "item_name": "x", "field": "y", "new_value": "z"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unknown section", resp.json()["detail"])

    def test_not_found_returns_404(self):
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/edit", json={
            "edits": [{"section": "summary", "item_name": "", "field": "", "new_value": "text"}]
        })
        self.assertEqual(resp.status_code, 404)


class TestAddProject(_BaseResumeTest):
    """Tests for POST /resume/{id}/add/project/{project_id}."""

    def setUp(self):
        super().setUp()
        patcher = patch(CTX_PATCH)
        self.mock_ctx = patcher.start()
        self.addCleanup(patcher.stop)

    def test_from_db_no_body(self):
        self.mock_doc.add_project.return_value = "Successfully added project 'WarframeFinderStreamlit'"
        self.mock_ctx.store.fetch_by_id.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/resume/test_abc123/add/project/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

    def test_body_overrides_db(self):
        self.mock_doc.add_project.return_value = "Successfully added project 'Custom'"
        self.mock_ctx.store.fetch_by_id.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/resume/test_abc123/add/project/1", json={"name": "Custom", "summary": "Override"})
        self.assertEqual(resp.status_code, 200)
        proj = self.mock_doc.add_project.call_args[0][0]
        self.assertEqual(proj.name, "Custom")
        self.assertEqual(proj.summary, "Override")

    def test_resume_not_found_returns_404(self):
        self._set_not_found()
        resp = self.client.post("/resume/fake_id/add/project/1")
        self.assertEqual(resp.status_code, 404)

    def test_db_record_not_found_returns_404(self):
        self.mock_ctx.store.fetch_by_id.return_value = None
        resp = self.client.post("/resume/test_abc123/add/project/999")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found in database", resp.json()["detail"])

    def test_no_resume_item_returns_400(self):
        self.mock_ctx.store.fetch_by_id.return_value = {"hierarchy": {}, "project_root": "C:\\some\\path"}
        resp = self.client.post("/resume/test_abc123/add/project/1")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("no resume_item", resp.json()["detail"])

    def test_unexpected_error_returns_500(self):
        self.mock_doc.add_project.side_effect = RuntimeError("disk full")
        self.mock_ctx.store.fetch_by_id.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/resume/test_abc123/add/project/1")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("disk full", resp.json()["detail"])


class TestDeleteResume(_BaseResumeTest):
    """Tests for DELETE /resume/{id}."""

    def test_success(self):
        self.mock_doc.yaml_file = MagicMock()
        resp = self.client.delete("/resume/test_abc123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("test_abc123", resp.json()["status"])

    def test_not_found_returns_404(self):
        self._set_not_found()
        resp = self.client.delete("/resume/fake_id")
        self.assertEqual(resp.status_code, 404)

    def test_os_error_returns_500(self):
        self.mock_doc.yaml_file.unlink.side_effect = OSError("Permission denied")
        resp = self.client.delete("/resume/test_abc123")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Permission denied", resp.json()["detail"])


if __name__ == "__main__":
    unittest.main()
