import unittest
import os
import gc
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.reporting.Generate_AI_RenderCV_portfolio import Create_Portfolio_RenderCV
from src.reporting.Generate_RenderCV_Resume import Project, Connections


class BasePortfolioTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gc.collect()
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            try:
                f.unlink(missing_ok=True)
            except PermissionError:
                pass

    def create_loaded_portfolio(self, auto_save=False):
        portfolio = Create_Portfolio_RenderCV(auto_save=auto_save)
        portfolio.generate_portfolio(name="Test User")
        portfolio.load_Protfolio_starter_file()
        return portfolio


class TestPortfolioInit(BasePortfolioTest):
    def test_init_default_values(self):
        portfolio = Create_Portfolio_RenderCV()
        self.assertTrue(portfolio.auto_save)
        self.assertIsNone(portfolio.data)

    def test_generate_and_load(self):
        portfolio = Create_Portfolio_RenderCV()
        self.assertEqual(portfolio.generate_portfolio(name="Test User"), "Success")
        self.assertTrue(portfolio.yaml_file.exists())
        data = portfolio.load_Protfolio_starter_file()
        self.assertIn('cv', data)

    def test_save_without_data_raises_error(self):
        with self.assertRaises(ValueError):
            Create_Portfolio_RenderCV().save()


class TestPortfolioConnections(BasePortfolioTest):
    def setUp(self):
        super().setUp()
        self.portfolio = self.create_loaded_portfolio()

    def test_add_connection(self):
        conn = Connections(network="Twitter", username="testuser")
        self.assertEqual(self.portfolio.add_new_portfolio_connection(conn), "Successfully added: Twitter")
        self.assertIn("already exists", self.portfolio.add_new_portfolio_connection(Connections(network="LinkedIn", username="x")))

    def test_modify_connection(self):
        self.assertEqual(self.portfolio.modify_portfolio_connection("LinkedIn", "new_user"), "Successfully updated: LinkedIn")
        self.assertIn("not found", self.portfolio.modify_portfolio_connection("Twitter", "user"))

    def test_remove_connection(self):
        self.assertEqual(self.portfolio.remove_portfolio_connection("LinkedIn"), "Successfully deleted: LinkedIn")
        self.assertIn("not found", self.portfolio.remove_portfolio_connection("Twitter"))


class TestPortfolioProjects(BasePortfolioTest):
    def setUp(self):
        super().setUp()
        self.portfolio = self.create_loaded_portfolio()

    def test_add_project(self):
        self.assertEqual(self.portfolio.add_portfolio_project(Project(name="New Project", summary="A new project")), "Successfully added: New Project")
        self.assertIn("already exists", self.portfolio.add_portfolio_project(Project(name="Project Name")))

    def test_modify_project(self):
        self.assertEqual(self.portfolio.modify_portfolio_project("Project Name", "summary", "New summary"), "Successfully modified: Project Name")
        self.assertIn("Invalid field", self.portfolio.modify_portfolio_project("Project Name", "invalid", "value"))

    def test_remove_project(self):
        self.assertEqual(self.portfolio.remove_portfolio_project("Nonexistent"), "Project not found: Nonexistent")
        self.assertEqual(self.portfolio.remove_portfolio_project("Project Name"), "Successfully deleted: Project Name")


class TestPortfolioAI(BasePortfolioTest):
    def setUp(self):
        super().setUp()
        self.portfolio = self.create_loaded_portfolio()

    def test_add_from_ai_without_data_raises_error(self):
        with self.assertRaises(ValueError):
            Create_Portfolio_RenderCV().add_portfolio_project_from_AI("path.json")

    @patch('src.reporting.Generate_AI_RenderCV_portfolio.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_AI_RenderCV_portfolio.orjson.loads')
    def test_add_from_ai_success(self, mock_orjson, mock_open, mock_resume):
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_open.return_value.__enter__.return_value.read.return_value = b'{}'
        mock_ai = MagicMock(project_title="AI Project", one_sentence_summary="AI summary", tech_stack="Python", key_responsibilities=["Task 1"])
        mock_resume.return_value.generate.return_value = mock_ai
        self.assertEqual(self.portfolio.add_portfolio_project_from_AI("project.json"), "Successfully added: AI Project")


class TestPortfolioAutoSaveAndRender(BasePortfolioTest):
    def test_auto_save_enabled(self):
        portfolio = self.create_loaded_portfolio(auto_save=True)
        with patch.object(portfolio, 'save') as mock_save:
            portfolio.add_portfolio_project(Project(name="Test", summary="Test"))
            mock_save.assert_called()

    def test_auto_save_disabled(self):
        portfolio = self.create_loaded_portfolio(auto_save=False)
        with patch.object(portfolio, 'save') as mock_save:
            portfolio.add_portfolio_project(Project(name="Test", summary="Test"))
            mock_save.assert_not_called()

    @patch('subprocess.run')
    def test_render_calls_subprocess(self, mock_run):
        portfolio = self.create_loaded_portfolio()
        mock_run.return_value = MagicMock(returncode=0)
        portfolio.render_portfolio()
        mock_run.assert_called_once()


if __name__ == '__main__':
    unittest.main()