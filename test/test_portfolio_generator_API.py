"""
Unit tests for Portfolio_Generator_API.py

Uses FastAPI's TestClient to simulate HTTP calls without running a real server.
All external dependencies (RenderCVDocument, runtimeAppContext) are mocked.
"""

import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient

from src.API.general_API import app

DOC_PATCH = "src.API.Portfolio_Generator_API.RenderCVDocument"
CTX_PATCH = "src.API.Portfolio_Generator_API.runtimeAppContext"

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


class _BasePortfolioTest(unittest.TestCase):
    """Shared setup: patches RenderCVDocument and creates a TestClient."""

    def setUp(self):
        self.client = TestClient(app)
        patcher = patch(DOC_PATCH)
        self.mock_doc_cls = patcher.start()
        self.mock_doc = MagicMock()
        self.mock_doc_cls.return_value = self.mock_doc
        self.addCleanup(patcher.stop)

    def _set_not_found(self):
        """Configure mock so _load_portfolio raises 404."""
        self.mock_doc.load.side_effect = FileNotFoundError


class TestGeneratePortfolio(_BasePortfolioTest):
    """Tests for POST /portfolio/generate."""

    def test_success(self):
        self.mock_doc.generate.return_value = "Generated"

        response = self.client.post("/portfolio/generate", json={"name": "John"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("portfolio_id", body)
        self.assertIn("John_", body["portfolio_id"])
        self.assertEqual(body["status"], "Portfolio created successfully")

    def test_success_with_theme(self):
        self.mock_doc.generate.return_value = "Generated"

        response = self.client.post("/portfolio/generate", json={"name": "John", "theme": "classic"})
        self.assertEqual(response.status_code, 200)
        self.mock_doc.update_theme.assert_called_once_with("classic")

    def test_already_exists_returns_409(self):
        self.mock_doc.generate.return_value = "Skipping generation"

        response = self.client.post("/portfolio/generate", json={"name": "John"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("overwrite=true", response.json()["detail"])

    def test_invalid_theme_returns_400(self):
        """Test that invalid theme on generate returns 400, not 500."""
        self.mock_doc.generate.return_value = "Generated"
        self.mock_doc.update_theme.side_effect = ValueError("Invalid theme 'bad'. Available: classic, sb2nov")

        response = self.client.post("/portfolio/generate", json={"name": "John", "theme": "bad"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid theme", response.json()["detail"])


class TestGetPortfolio(_BasePortfolioTest):
    """Tests for GET /portfolio/{id}."""

    def test_success(self):
        response = self.client.get("/portfolio/test_abc123")
        self.assertEqual(response.status_code, 200)
        for key in ["name", "contact", "theme", "summary",
                     "projects", "skills", "connections"]:
            self.assertIn(key, response.json())

    def test_not_found_returns_404(self):
        self._set_not_found()
        response = self.client.get("/portfolio/fake_id")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])


class TestEditPortfolio(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/edit."""

    def _post_edit(self, edits):
        return self.client.post("/portfolio/test_abc123/edit", json={"edits": edits})

    def test_all_sections(self):
        """Single test covering every valid section type including projects."""
        self.mock_doc.modify_skill.return_value = "Successfully modified skill"
        self.mock_doc.update_summary.return_value = "Successfully updated summary"
        self.mock_doc.update_theme.return_value = "Successfully updated theme"
        self.mock_doc.modify_project.return_value = "Successfully modified project field"

        resp = self._post_edit([
            {"section": "skills", "item_name": "Python", "field": "", "new_value": "Python 3.12"},
            {"section": "summary", "item_name": "", "field": "", "new_value": "New text"},
            {"section": "contact", "item_name": "", "field": "email", "new_value": "a@b.com"},
            {"section": "theme", "item_name": "", "field": "", "new_value": "classic"},
            {"section": "projects", "item_name": "MyProject", "field": "summary", "new_value": "Updated summary"},
        ])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 5)
        self.mock_doc.modify_project.assert_called_once_with("MyProject", "summary", "Updated summary")

    def test_invalid_theme_returns_400(self):
        """Test that invalid theme in edit returns 400, not 500."""
        self.mock_doc.update_theme.side_effect = ValueError("Invalid theme 'bad'. Available: classic, sb2nov")

        resp = self._post_edit([
            {"section": "theme", "item_name": "", "field": "", "new_value": "bad"}
        ])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid theme", resp.json()["detail"])

    def test_unknown_section_returns_400(self):
        resp = self._post_edit([{"section": "invalid", "item_name": "x", "field": "y", "new_value": "z"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unknown section", resp.json()["detail"])

    def test_not_found_returns_404(self):
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/edit", json={
            "edits": [{"section": "summary", "item_name": "", "field": "", "new_value": "text"}]
        })
        self.assertEqual(resp.status_code, 404)


class TestAddProject(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/add/project/{project_id}."""

    def setUp(self):
        super().setUp()
        patcher = patch(CTX_PATCH)
        self.mock_ctx = patcher.start()
        self.addCleanup(patcher.stop)

    def test_from_db_success(self):
        self.mock_doc.add_project.return_value = "Successfully added project 'WarframeFinderStreamlit'"
        self.mock_ctx.store.fetch_by_id.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/portfolio/test_abc123/add/project/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

    def test_missing_data_returns_404(self):
        """Test 404 for missing DB record and missing resume_item."""
        # DB record not found
        self.mock_ctx.store.fetch_by_id.return_value = None
        resp = self.client.post("/portfolio/test_abc123/add/project/999")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found in database", resp.json()["detail"])

        # Record exists but no resume_item
        self.mock_ctx.store.fetch_by_id.return_value = {"hierarchy": {}, "project_root": "C:\\some\\path"}
        resp = self.client.post("/portfolio/test_abc123/add/project/1")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("no resume_item", resp.json()["detail"])

    def test_unexpected_error_returns_500(self):
        self.mock_doc.add_project.side_effect = RuntimeError("disk full")
        self.mock_ctx.store.fetch_by_id.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/portfolio/test_abc123/add/project/1")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("disk full", resp.json()["detail"])


class TestRenderPortfolio(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/render/{format}."""

    @patch("src.API.Portfolio_Generator_API.shutil")
    def test_success(self, _mock_shutil):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_pdf = Path(tmp_dir) / "portfolio.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake content")
            self.mock_doc.render_outputs.return_value = ("successfully rendered", {"pdf": [fake_pdf]})

            resp = self.client.post("/portfolio/test_abc123/render/pdf")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("X-Portfolio-ID", resp.headers)
            self.assertEqual(resp.headers["content-type"], "application/pdf")

    def test_error_cases(self):
        """Test 404 for missing portfolio and 500 for render failure."""
        # Portfolio not found
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/render/pdf")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # Render failure
        self.mock_doc.load.side_effect = None  # Reset to allow load
        self.mock_doc.render_outputs.return_value = ("Render failed", {})
        resp = self.client.post("/portfolio/test_abc123/render/pdf")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Render failed", resp.json()["detail"])


class TestDeletePortfolio(_BasePortfolioTest):
    """Tests for DELETE /portfolio/{id}."""

    def test_success(self):
        self.mock_doc.yaml_file = MagicMock()
        resp = self.client.delete("/portfolio/test_abc123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("test_abc123", resp.json()["status"])

    def test_error_cases(self):
        """Test 404 for missing portfolio and 500 for OS error."""
        # Portfolio not found
        self._set_not_found()
        resp = self.client.delete("/portfolio/fake_id")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # OS error during deletion
        self.mock_doc.load.side_effect = None  # Reset to allow load
        self.mock_doc.yaml_file.unlink.side_effect = OSError("Permission denied")
        resp = self.client.delete("/portfolio/test_abc123")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Permission denied", resp.json()["detail"])


if __name__ == "__main__":
    unittest.main()
