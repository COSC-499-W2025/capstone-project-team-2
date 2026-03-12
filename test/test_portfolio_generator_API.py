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
AI_PATCH = "src.API.Portfolio_Generator_API.GenerateResumeAI_Ver2"

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

    def test_add_connection(self):
        """Adding a new connection via edit calls add_connection."""
        self.mock_doc.get_connections.return_value = []
        self.mock_doc.add_connection.return_value = "Successfully added: GitHub"

        resp = self._post_edit([
            {"section": "connections", "item_name": "GitHub", "field": "username", "new_value": "jdoe"}
        ])
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.add_connection.assert_called_once()

    def test_modify_connection(self):
        """Modifying an existing connection via edit calls modify_connection."""
        self.mock_doc.get_connections.return_value = [{"network": "GitHub", "username": "old"}]
        self.mock_doc.modify_connection.return_value = "Successfully updated: GitHub"

        resp = self._post_edit([
            {"section": "connections", "item_name": "GitHub", "field": "username", "new_value": "newuser"}
        ])
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.modify_connection.assert_called_once_with("GitHub", "newuser")

    def test_remove_connection(self):
        """Removing a connection via edit with field='delete' calls remove_connection."""
        self.mock_doc.remove_connection.return_value = "Successfully deleted: GitHub"

        resp = self._post_edit([
            {"section": "connections", "item_name": "GitHub", "field": "delete", "new_value": ""}
        ])
        self.assertEqual(resp.status_code, 200)
        self.mock_doc.remove_connection.assert_called_once_with("GitHub")

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
    """Tests for POST /portfolio/{id}/add/project/{project_name}."""

    def setUp(self):
        super().setUp()
        patcher = patch(CTX_PATCH)
        self.mock_ctx = patcher.start()
        self.addCleanup(patcher.stop)

    def test_from_db_success(self):
        self.mock_doc.add_project.return_value = "Successfully added project 'WarframeFinderStreamlit'"
        self.mock_ctx.store.fetch_by_name.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

    def test_missing_data_returns_404(self):
        """Test 404 for missing DB record and missing resume_item."""
        # DB record not found
        self.mock_ctx.store.fetch_by_name.return_value = None
        resp = self.client.post("/portfolio/test_abc123/add/project/UnknownProject")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found in database", resp.json()["detail"])

        # Record exists but no resume_item
        self.mock_ctx.store.fetch_by_name.return_value = {"hierarchy": {}, "project_root": "C:\\some\\path"}
        resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("no resume_item", resp.json()["detail"])

    def test_unexpected_error_returns_500(self):
        self.mock_doc.add_project.side_effect = RuntimeError("disk full")
        self.mock_ctx.store.fetch_by_name.return_value = SAMPLE_DB_RECORD

        resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("disk full", resp.json()["detail"])


class TestAddProjectManual(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/add/project/manual."""

    def test_all_cases(self):
        """Covers success (all fields), success (name only), missing name (422), bad result (400), error (500), not found (404)."""
        # All fields
        self.mock_doc.add_project.return_value = "Successfully added project 'My Side Project'"
        resp = self.client.post("/portfolio/test_abc123/add/project/manual", json={
            "name": "My Side Project", "start_date": "2024-01", "end_date": "2025-03",
            "location": "Vancouver, BC", "summary": "Explore Rust.", "highlights": ["Built async runtime"],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])
        self.mock_doc.add_project.assert_called_once()

        # Name only
        self.mock_doc.add_project.return_value = "Successfully added project 'Minimal'"
        resp = self.client.post("/portfolio/test_abc123/add/project/manual", json={"name": "Minimal"})
        self.assertEqual(resp.status_code, 200)

        # Missing name → 422
        resp = self.client.post("/portfolio/test_abc123/add/project/manual", json={"summary": "No name"})
        self.assertEqual(resp.status_code, 422)

        # Bad result → 400
        self.mock_doc.add_project.return_value = "Failed: duplicate project name"
        resp = self.client.post("/portfolio/test_abc123/add/project/manual", json={"name": "Duplicate"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("duplicate project name", resp.json()["detail"])

        # Unexpected error → 500
        self.mock_doc.add_project.side_effect = RuntimeError("disk full")
        resp = self.client.post("/portfolio/test_abc123/add/project/manual", json={"name": "My Project"})
        self.assertEqual(resp.status_code, 500)
        self.assertIn("disk full", resp.json()["detail"])

        # Portfolio not found → 404
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/add/project/manual", json={"name": "My Project"})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])


class TestRenderPortfolio(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/render/{format}."""

    @patch("src.API.Portfolio_Generator_API.shutil")
    def test_render_all_formats(self, _mock_shutil):
        """Test rendering in all supported formats: pdf, html, markdown."""
        format_cases = [
            ("pdf", "portfolio.pdf", b"%PDF-1.4 fake", "application/pdf"),
            ("html", "portfolio.html", b"<html>test</html>", "text/html; charset=utf-8"),
            ("markdown", "portfolio.md", b"# Portfolio", "text/markdown; charset=utf-8"),
        ]
        for fmt, filename, content, expected_type in format_cases:
            with self.subTest(format=fmt), tempfile.TemporaryDirectory() as tmp_dir:
                fake_file = Path(tmp_dir) / filename
                fake_file.write_bytes(content)
                self.mock_doc.render_outputs.return_value = (
                    "successfully rendered",
                    {fmt: [fake_file]},
                )

                resp = self.client.post(f"/portfolio/test_abc123/render/{fmt}")
                self.assertEqual(resp.status_code, 200)
                self.assertIn("X-Portfolio-ID", resp.headers)
                self.assertEqual(resp.headers["content-type"], expected_type)

    def test_render_error_cases(self):
        """Test unsupported format (400), not found (404), and render failure (500)."""
        # Unsupported format
        resp = self.client.post("/portfolio/test_abc123/render/docx")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported format", resp.json()["detail"])

        # Portfolio not found
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/render/pdf")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # Render failure
        self.mock_doc.load.side_effect = None
        self.mock_doc.render_outputs.return_value = ("Render failed", {"pdf": []})
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


class TestPortfolioShowcaseRoleAPI(_BasePortfolioTest):
    """Tests for project-level portfolio showcase role overrides."""

    @patch("src.API.Portfolio_Generator_API.save_project_role_override")
    def test_set_role_success(self, mock_save):
        mock_save.return_value = {"project": {"role": "Team Lead"}}
        resp = self.client.post(
            "/portfolio-showcase/MyProject/role",
            json={"role": "Team Lead"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["project_name"], "MyProject")
        self.assertEqual(resp.json()["role"], "Team Lead")
        mock_save.assert_called_once_with("MyProject", "Team Lead")

    def test_set_role_empty_returns_400(self):
        resp = self.client.post(
            "/portfolio-showcase/MyProject/role",
            json={"role": "   "},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot be empty", resp.json()["detail"])

    @patch("src.API.Portfolio_Generator_API.load_portfolio_showcase")
    def test_get_role_success(self, mock_load):
        mock_load.return_value = {"project": {"role": "Backend Developer"}}
        resp = self.client.get("/portfolio-showcase/MyProject/role")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["project_name"], "MyProject")
        self.assertEqual(resp.json()["role"], "Backend Developer")

    @patch("src.API.Portfolio_Generator_API.load_portfolio_showcase")
    def test_get_role_not_found_returns_404(self, mock_load):
        mock_load.return_value = {}
        resp = self.client.get("/portfolio-showcase/UnknownProject/role")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("No saved role", resp.json()["detail"])


class TestRemoveProject(_BasePortfolioTest):
    """Tests for DELETE /portfolio/{id}/project/{project_name}."""

    def test_success_and_error_cases(self):
        """Covers success, project not found, no projects, and portfolio not found."""
        # Success
        self.mock_doc.remove_project.return_value = "Successfully removed project 'MyProject'"
        resp = self.client.delete("/portfolio/test_abc123/project/MyProject")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # Project not found
        self.mock_doc.remove_project.return_value = "Project 'Unknown' not found"
        resp = self.client.delete("/portfolio/test_abc123/project/Unknown")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # No projects at all
        self.mock_doc.remove_project.return_value = "No projects in portfolio"
        resp = self.client.delete("/portfolio/test_abc123/project/SomeProject")
        self.assertEqual(resp.status_code, 404)

        # Portfolio itself not found
        self._set_not_found()
        resp = self.client.delete("/portfolio/fake_id/project/MyProject")
        self.assertEqual(resp.status_code, 404)


class TestAddProjectExtended(_BasePortfolioTest):
    """Tests for add-project overrides, _check_result failure, and default render."""

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
            "/portfolio/test_abc123/add/project/WarframeFinderStreamlit",
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
        self.mock_doc.add_project.return_value = "Failed: duplicate project name"
        resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("duplicate project name", resp.json()["detail"])

    @patch("src.API.Portfolio_Generator_API.shutil")
    def test_default_render_and_showcase_save_error(self, _mock_shutil):
        """Covers default render (no format) returning PDF and showcase role save error."""
        # Default render uses PDF
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_pdf = Path(tmp_dir) / "portfolio.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            self.mock_doc.render_outputs.return_value = (
                "successfully rendered",
                {"pdf": [fake_pdf]},
            )
            resp = self.client.post("/portfolio/test_abc123/render")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers["content-type"], "application/pdf")
            self.assertIn("X-Portfolio-ID", resp.headers)

    @patch("src.API.Portfolio_Generator_API.save_project_role_override")
    def test_showcase_role_save_error_returns_500(self, mock_save):
        """Test 500 when save_project_role_override raises an exception."""
        mock_save.side_effect = RuntimeError("DB connection lost")
        resp = self.client.post(
            "/portfolio-showcase/MyProject/role",
            json={"role": "Team Lead"},
        )
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Failed to save role override", resp.json()["detail"])


class TestExportPortfolioErrors(_BasePortfolioTest):
    """Test export endpoints return 404 for missing portfolios."""

    def test_export_not_found_cases(self):
        """Both default and custom export return 404 for missing portfolios."""
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/export/pdf")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        resp = self.client.post("/portfolio/fake_id/export/pdf/custom", json={"path": "/tmp"})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])


class TestExportPortfolio(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/export/{format} and /portfolio/{id}/export/{format}/custom."""

    @patch("src.API.Portfolio_Generator_API.shutil")
    @patch("src.API.Portfolio_Generator_API.RENDERED_OUTPUTS_DIR")
    def test_save_default_and_custom(self, mock_dir, mock_shutil):
        """Save to default and custom directories both return a success status and path."""
        mock_dir.mkdir = MagicMock()
        mock_dir.__truediv__ = lambda self, name: Path("/fake/rendered_outputs") / name

        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as custom_dir:
            fake_pdf = Path(tmp_dir) / "portfolio.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            self.mock_doc.render_outputs.return_value = ("successfully rendered", {"pdf": [fake_pdf]})

            # Default directory
            resp = self.client.post("/portfolio/test_abc123/export/pdf")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Saved successfully", resp.json()["status"])
            self.assertIn("path", resp.json())

            # Custom directory
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            resp = self.client.post("/portfolio/test_abc123/export/pdf/custom", json={"path": custom_dir})
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Saved successfully", resp.json()["status"])
            self.assertIn(custom_dir.replace("\\", "/"), resp.json()["path"].replace("\\", "/"))

    def test_save_custom_invalid_dir(self):
        """Save to non-existent directory returns 400."""
        resp = self.client.post("/portfolio/test_abc123/export/pdf/custom", json={"path": "/nonexistent/dir"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("does not exist", resp.json()["detail"])

    def test_save_unsupported_format(self):
        """Save with unsupported format returns 400."""
        resp = self.client.post("/portfolio/test_abc123/export/docx")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported format", resp.json()["detail"])


class TestSkillEndpoints(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/add/skill, POST /portfolio/{id}/skill/{label}/append, DELETE /portfolio/{id}/skill/{label}."""

    def test_add_skill(self):
        """Covers success, duplicate (409), failure (400), and portfolio not found (404)."""
        # Success
        self.mock_doc.add_skills.return_value = "Successfully added skills"
        resp = self.client.post("/portfolio/test_abc123/add/skill", json={
            "label": "Languages",
            "details": "Python, Java, C++",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "Successfully added skills")
        call_args = self.mock_doc.add_skills.call_args
        skill_arg = call_args[0][0]
        self.assertEqual(skill_arg.label, "Languages")
        self.assertEqual(skill_arg.details, "Python, Java, C++")

        # Duplicate label returns 409
        self.mock_doc.add_skills.return_value = "Duplicate label 'Languages' already exists"
        resp = self.client.post("/portfolio/test_abc123/add/skill", json={
            "label": "Languages",
            "details": "Python",
        })
        self.assertEqual(resp.status_code, 409)
        self.assertIn("Duplicate", resp.json()["detail"])

        # Generic failure returns 400
        self.mock_doc.add_skills.return_value = "Label cannot be empty"
        resp = self.client.post("/portfolio/test_abc123/add/skill", json={
            "label": "Languages",
            "details": "Python",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Label cannot be empty", resp.json()["detail"])

        # Portfolio not found
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/add/skill", json={
            "label": "Languages",
            "details": "Python",
        })
        self.assertEqual(resp.status_code, 404)

    def test_append_skill(self):
        """Covers append success (merges details), skill not found (404), and portfolio not found (404)."""
        # Success — appends to existing details
        self.mock_doc.get_skills.return_value = [
            {"label": "Languages", "details": "Python, Java"}
        ]
        self.mock_doc.modify_skill.return_value = "Successfully modified skill"
        resp = self.client.post("/portfolio/test_abc123/skill/Languages/append", json={
            "details": "C++",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["details"], "Python, Java, C++")
        self.assertIn("Successfully", resp.json()["status"])
        self.mock_doc.modify_skill.assert_called_once_with("Languages", "Python, Java, C++")

        # Skill label not found returns 404
        self.mock_doc.get_skills.return_value = []
        resp = self.client.post("/portfolio/test_abc123/skill/Unknown/append", json={
            "details": "Rust",
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # Portfolio not found
        self._set_not_found()
        resp = self.client.post("/portfolio/fake_id/skill/Languages/append", json={
            "details": "Rust",
        })
        self.assertEqual(resp.status_code, 404)

    def test_remove_skill(self):
        """Covers remove success, label not found (404), no skills (404), and portfolio not found (404)."""
        # Success
        self.mock_doc.remove_skill.return_value = "Successfully removed skill 'Languages'"
        resp = self.client.delete("/portfolio/test_abc123/skill/Languages")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Successfully", resp.json()["status"])

        # Label not found returns 404
        self.mock_doc.remove_skill.return_value = "Skill 'Unknown' not found"
        resp = self.client.delete("/portfolio/test_abc123/skill/Unknown")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"])

        # No skills on the portfolio returns 404
        self.mock_doc.remove_skill.return_value = "No skills in portfolio"
        resp = self.client.delete("/portfolio/test_abc123/skill/Languages")
        self.assertEqual(resp.status_code, 404)

        # Portfolio not found
        self._set_not_found()
        resp = self.client.delete("/portfolio/fake_id/skill/Languages")
        self.assertEqual(resp.status_code, 404)


class TestListPortfolios(_BasePortfolioTest):
    """Tests for GET /portfolios."""

    @patch("src.API.Portfolio_Generator_API.Path")
    def test_list_portfolios(self, MockPath):
        """Returns 200 with a list; entries have id, name, and created_at when files exist."""
        import io

        # Empty list when no YAML files
        mock_cv_dir = MagicMock()
        mock_cv_dir.glob.return_value = []
        MockPath.return_value.resolve.return_value.parents.__getitem__.return_value \
            .__truediv__.return_value.__truediv__.return_value = mock_cv_dir

        resp = self.client.get("/portfolios")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

        # Populated list with expected fields
        fake_yaml = MagicMock()
        fake_yaml.stem = "Jane_Doe_abc12345_Portfolio_CV"
        mock_cv_dir.glob.return_value = [fake_yaml]

        with patch("builtins.open", MagicMock(return_value=io.StringIO("created_at: '2025-01-01T00:00:00Z'\n"))):
            resp = self.client.get("/portfolios")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        if data:
            for key in ("id", "name", "created_at"):
                self.assertIn(key, data[0])


class TestAddProjectAI(_BasePortfolioTest):
    """Tests for POST /portfolio/{id}/add/project/{project_name}/ai."""

    def _make_ai_entry(self, tech_stack="Python, FastAPI"):
        entry = MagicMock()
        entry.one_sentence_summary = "Built a REST API with FastAPI."
        entry.tech_stack = tech_stack
        entry.project_title = "WarframeFinder"
        entry.key_responsibilities = ["Built endpoints", "Wrote unit tests"]
        return entry

    def test_success_and_summary_variants(self):
        """Success adds project; tech_stack is appended when present and omitted when falsy."""
        with patch(AI_PATCH) as MockAI:
            mock_gen = MagicMock()
            MockAI.return_value = mock_gen
            mock_gen.project_exists = True
            self.mock_doc.add_project.return_value = "Successfully added project 'WarframeFinder'"

            # With tech stack
            mock_gen.generate_AI_Resume_entry.return_value = self._make_ai_entry()
            resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit/ai")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Successfully", resp.json()["status"])
            proj = self.mock_doc.add_project.call_args[0][0]
            self.assertIn("Tech stack:", proj.summary)

            # Without tech stack
            self.mock_doc.add_project.reset_mock()
            mock_gen.generate_AI_Resume_entry.return_value = self._make_ai_entry(tech_stack=None)
            self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit/ai")
            proj = self.mock_doc.add_project.call_args[0][0]
            self.assertNotIn("Tech stack:", proj.summary)

    def test_error_cases(self):
        """Covers project not found (404), AI returns None (400), AI exception (500), add_project failure (500), portfolio not found (404)."""
        with patch(AI_PATCH) as MockAI:
            mock_gen = MagicMock()
            MockAI.return_value = mock_gen

            # Project not found
            mock_gen.project_exists = False
            resp = self.client.post("/portfolio/test_abc123/add/project/Unknown/ai")
            self.assertEqual(resp.status_code, 404)
            self.assertIn("not found", resp.json()["detail"])

            # AI returns None → 400
            mock_gen.project_exists = True
            mock_gen.generate_AI_Resume_entry.return_value = None
            resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit/ai")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("no data", resp.json()["detail"])

            # AI raises exception → 500
            mock_gen.generate_AI_Resume_entry.side_effect = RuntimeError("API quota exceeded")
            resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit/ai")
            self.assertEqual(resp.status_code, 500)
            self.assertIn("API quota exceeded", resp.json()["detail"])

            # add_project raises exception → 500
            mock_gen.generate_AI_Resume_entry.side_effect = None
            mock_gen.generate_AI_Resume_entry.return_value = self._make_ai_entry()
            self.mock_doc.add_project.side_effect = RuntimeError("disk full")
            resp = self.client.post("/portfolio/test_abc123/add/project/WarframeFinderStreamlit/ai")
            self.assertEqual(resp.status_code, 500)
            self.assertIn("disk full", resp.json()["detail"])

        # Portfolio not found → 404
        self._set_not_found()
        with patch(AI_PATCH) as MockAI:
            resp = self.client.post("/portfolio/fake_id/add/project/WarframeFinderStreamlit/ai")
            self.assertEqual(resp.status_code, 404)
            MockAI.assert_not_called()


if __name__ == "__main__":
    unittest.main()
