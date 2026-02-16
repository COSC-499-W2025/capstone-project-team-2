import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.reporting.portfolio_rendercv_service import PortfolioRenderCVService
from src.reporting.portfolio_service import PortfolioShowcase

class TestPortfolioRenderCVService(unittest.TestCase):
    """Unit tests for PortfolioRenderCVService."""

    def setUp(self):
        """Common setup for tests."""
        self.mock_cv = MagicMock()
        self.mock_cv.current_projects = []
        self.mock_cv.current_connections = []
        self.mock_cv.data = {"cv": {}}

        self.sample_showcase = PortfolioShowcase(
            title="Test Project",
            overview="A test portfolio project",
            role="Developer",
            technical_highlights=[
                "Built scalable backend",
                "Implemented CI/CD pipeline",
            ],
            design_quality={
                "oop_comment": "Well-structured and modular"
            },
            evidence={},
            skills=["Python"],
            contributors=["Alice", "Bob"],
        )

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_service_initialization(self, mock_render_cv_document):
        """Service initializes and loads starter file."""
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")

        mock_render_cv_document.assert_called_once_with(doc_type='portfolio', auto_save=True)
        self.mock_cv.generate.assert_called_once_with(name="Test User")
        self.mock_cv.load.assert_called_once_with(name="Test User")

    def test_build_rendercv_project(self):
        """PortfolioShowcase is converted to RenderCV Project."""
        project = PortfolioRenderCVService.build_rendercv_project(
            self.sample_showcase
        )

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.summary, "A test portfolio project")

        self.assertIn("Built scalable backend", project.highlights)
        self.assertIn("Implemented CI/CD pipeline", project.highlights)
        self.assertIn(
            "OOP Design: Well-structured and modular",
            project.highlights,
        )
        self.assertIn(
            "Contributors: Alice, Bob",
            project.highlights,
        )

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_add_portfolio(self, mock_render_cv_document):
        """Adding a portfolio project delegates to RenderCV."""
        mock_render_cv_document.return_value = self.mock_cv
        self.mock_cv.add_project.return_value = "Successfully added"

        service = PortfolioRenderCVService(name="Test User")
        result = service.add_portfolio(self.sample_showcase)

        self.mock_cv.add_project.assert_called_once()
        self.assertEqual(result, "Successfully added")

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_list_portfolios(self, mock_render_cv_document):
        """List all portfolio projects."""
        self.mock_cv.current_projects = [
            {"name": "Project A"},
            {"name": "Project B"},
        ]
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        projects = service.list_portfolios()

        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["name"], "Project A")

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_get_portfolio_found(self, mock_render_cv_document):
        """Retrieve an existing portfolio project."""
        self.mock_cv.current_projects = [
            {"name": "Project A"},
            {"name": "Project B"},
        ]
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        project = service.get_portfolio("Project B")

        self.assertIsNotNone(project)
        self.assertEqual(project["name"], "Project B")

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_get_portfolio_not_found(self, mock_render_cv_document):
        """Return None when portfolio project does not exist."""
        self.mock_cv.current_projects = [{"name": "Project A"}]
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        project = service.get_portfolio("Missing Project")

        self.assertIsNone(project)

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_update_portfolio(self, mock_render_cv_document):
        """Update a portfolio project field."""
        self.mock_cv.modify_project.return_value = "Updated successfully"
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        result = service.update_portfolio(
            project_name="Test Project",
            field="summary",
            value="Updated summary",
        )

        self.mock_cv.modify_project.assert_called_once_with(
            project_name="Test Project",
            field="summary",
            new_value="Updated summary",
        )
        self.assertEqual(result, "Updated successfully")

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_delete_portfolio(self, mock_render_cv_document):
        """Delete a portfolio project."""
        self.mock_cv.remove_project.return_value = "Deleted successfully"
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        result = service.delete_portfolio("Test Project")

        self.mock_cv.remove_project.assert_any_call("Test Project")
        self.assertEqual(result, "Deleted successfully")

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_render_portfolio_pdf(self, mock_render_cv_document):
        """Render portfolio PDF via RenderCV."""
        self.mock_cv.render_outputs.return_value = ("successfully rendered", {"pdf": [Path("/fake/path.pdf")]})
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        result = service.render_portfolio_pdf()

        self.mock_cv.render_outputs.assert_called_once_with(formats=["pdf"])
        self.assertEqual(result[0], "successfully rendered")

    @patch("src.reporting.portfolio_rendercv_service.RenderCVDocument")
    def test_render_portfolio_outputs(self, mock_render_cv_document):
        """Render portfolio outputs via RenderCV."""
        self.mock_cv.render_outputs.return_value = ("ok", {"html": [Path("/fake/path.html")]})
        mock_render_cv_document.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        status, outputs = service.render_portfolio_outputs(["html"])

        self.mock_cv.render_outputs.assert_called_once_with(formats=["html"])
        self.assertEqual(status, "ok")
        self.assertIn("html", outputs)


if __name__ == "__main__":
    unittest.main()
