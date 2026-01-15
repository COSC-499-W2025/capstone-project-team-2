import unittest
from unittest.mock import MagicMock, patch

from src.reporting.portfolio_rendercv_service import PortfolioRenderCVService
from src.reporting.portfolio_service import PortfolioShowcase

class TestPortfolioRenderCVService(unittest.TestCase):
    """Unit tests for PortfolioRenderCVService."""

    def setUp(self):
        """Common setup for tests."""
        self.mock_cv = MagicMock()
        self.mock_cv.current_projects = []

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

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_service_initialization(self, mock_create_render_cv):
        """Service initializes and loads starter file."""
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")

        mock_create_render_cv.assert_called_once()
        self.mock_cv.generate_starter_file.assert_called_once_with(name="Test User")
        self.mock_cv.load_starter_file.assert_called_once_with(name="Test User")

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

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_add_portfolio(self, mock_create_render_cv):
        """Adding a portfolio project delegates to RenderCV."""
        mock_create_render_cv.return_value = self.mock_cv
        self.mock_cv.add_project.return_value = "Successfully added"

        service = PortfolioRenderCVService(name="Test User")
        result = service.add_portfolio(self.sample_showcase)

        self.mock_cv.add_project.assert_called_once()
        self.assertEqual(result, "Successfully added")

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_list_portfolios(self, mock_create_render_cv):
        """List all portfolio projects."""
        self.mock_cv.current_projects = [
            {"name": "Project A"},
            {"name": "Project B"},
        ]
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        projects = service.list_portfolios()

        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["name"], "Project A")

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_get_portfolio_found(self, mock_create_render_cv):
        """Retrieve an existing portfolio project."""
        self.mock_cv.current_projects = [
            {"name": "Project A"},
            {"name": "Project B"},
        ]
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        project = service.get_portfolio("Project B")

        self.assertIsNotNone(project)
        self.assertEqual(project["name"], "Project B")

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_get_portfolio_not_found(self, mock_create_render_cv):
        """Return None when portfolio project does not exist."""
        self.mock_cv.current_projects = [{"name": "Project A"}]
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        project = service.get_portfolio("Missing Project")

        self.assertIsNone(project)

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_update_portfolio(self, mock_create_render_cv):
        """Update a portfolio project field."""
        self.mock_cv.modify_projects_info.return_value = "Updated successfully"
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        result = service.update_portfolio(
            project_name="Test Project",
            field="summary",
            value="Updated summary",
        )

        self.mock_cv.modify_projects_info.assert_called_once_with(
            project_name="Test Project",
            field="summary",
            new_value="Updated summary",
        )
        self.assertEqual(result, "Updated successfully")

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_delete_portfolio(self, mock_create_render_cv):
        """Delete a portfolio project."""
        self.mock_cv.delete_project.return_value = "Deleted successfully"
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        result = service.delete_portfolio("Test Project")

        self.mock_cv.delete_project.assert_called_once_with("Test Project")
        self.assertEqual(result, "Deleted successfully")

    @patch("src.reporting.portfolio_rendercv_service.create_Render_CV")
    def test_render_portfolio_pdf(self, mock_create_render_cv):
        """Render portfolio PDF via RenderCV."""
        self.mock_cv.render_CV.return_value = (
            "successfully rendered",
            "/fake/path.pdf",
        )
        mock_create_render_cv.return_value = self.mock_cv

        service = PortfolioRenderCVService(name="Test User")
        result = service.render_portfolio_pdf()

        self.mock_cv.render_CV.assert_called_once()
        self.assertEqual(result[0], "successfully rendered")


if __name__ == "__main__":
    unittest.main()
