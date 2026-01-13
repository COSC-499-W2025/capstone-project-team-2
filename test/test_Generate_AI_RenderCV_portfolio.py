import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.reporting.Generate_AI_RenderCV_portfolio import Create_Portfolio_RenderCV
from src.reporting.Generate_RenderCV_Resume import Project, Connections


class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_load_and_save(self):
        portfolio = Create_Portfolio_RenderCV()
        portfolio.cv_files_dir = Path(self.test_dir)
        self.assertEqual(portfolio.generate_portfolio(name="Test User"), "Success")
        self.assertTrue(portfolio.yaml_file.exists())
        data = portfolio.load_Protfolio_starter_file()
        self.assertIn('cv', data)

    def test_add_connection_and_project(self):
        portfolio = Create_Portfolio_RenderCV(auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate_portfolio(name="Test User")
        portfolio.load_Protfolio_starter_file()
        self.assertEqual(portfolio.add_new_portfolio_connection(Connections(network="Twitter", username="test")), "Successfully added: Twitter")
        self.assertEqual(portfolio.add_portfolio_project(Project(name="New Project", summary="Test")), "Successfully added: New Project")

    @patch('src.reporting.Generate_AI_RenderCV_portfolio.GenerateProjectResume')
    @patch('src.reporting.Generate_AI_RenderCV_portfolio.orjson.loads')
    def test_add_project_from_ai(self, mock_orjson, mock_resume):
        portfolio = Create_Portfolio_RenderCV(auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate_portfolio(name="Test User")
        portfolio.load_Protfolio_starter_file()

        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_resume.return_value.generate.return_value = MagicMock(
            project_title="AI Project", one_sentence_summary="Summary", tech_stack="Python", key_responsibilities=["Task"])

        m = mock_open(read_data=b'{}')
        with patch('builtins.open', m):
            result = portfolio.add_portfolio_project_from_AI("project.json")

        self.assertEqual(result, "Successfully added: AI Project")


if __name__ == '__main__':
    unittest.main()