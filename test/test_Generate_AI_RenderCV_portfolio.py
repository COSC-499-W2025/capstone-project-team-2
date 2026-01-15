import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.reporting.Generate_AI_RenderCV_portfolio import Create_Portfolio_RenderCV
from src.reporting.Generate_RenderCV_Resume import Project, Connections


class TestPortfolio(unittest.TestCase):
    """
    Test suite for the Create_Portfolio_RenderCV class.

    Tests portfolio generation, loading, saving, and adding connections/projects
    functionality including AI-generated project additions.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.

        Creates a temporary directory and changes the working directory to it
        for isolated test execution.

        Args:
            self: The test case instance

        Returns:
            None: Sets up instance attributes test_dir and original_cwd
        """
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """
        Clean up test fixtures after each test method.

        Restores the original working directory and removes the temporary
        test directory to ensure clean state for subsequent tests.

        Args:
            self: The test case instance

        Returns:
            None: Cleans up test environment
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_load_and_save(self):
        """
        Test portfolio generation, file creation, and loading functionality.

        Verifies that a portfolio can be successfully generated with a given name,
        the YAML file is created on disk, and the loaded data contains the expected
        'cv' key structure.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if portfolio generates, saves, and loads correctly
        """
        portfolio = Create_Portfolio_RenderCV()
        portfolio.cv_files_dir = Path(self.test_dir)
        self.assertEqual(portfolio.generate_portfolio(name="Test User"), "Success")
        self.assertTrue(portfolio.yaml_file.exists())
        data = portfolio.load_Protfolio_starter_file()
        self.assertIn('cv', data)

    def test_add_connection_and_project(self):
        """
        Test adding social connections and projects to an existing portfolio.

        Verifies that new social network connections and projects can be
        successfully added to a generated portfolio, with appropriate
        success messages returned for each addition.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if connections and projects are added successfully
        """
        portfolio = Create_Portfolio_RenderCV(auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate_portfolio(name="Test User")
        portfolio.load_Protfolio_starter_file()
        self.assertEqual(portfolio.add_new_portfolio_connection(Connections(network="Twitter", username="test")), "Successfully added: Twitter")
        self.assertEqual(portfolio.add_portfolio_project(Project(name="New Project", summary="Test")), "Successfully added: New Project")

    @patch('src.reporting.Generate_AI_RenderCV_portfolio.GenerateProjectResume')
    @patch('src.reporting.Generate_AI_RenderCV_portfolio.orjson.loads')
    def test_add_project_from_ai(self, mock_orjson, mock_resume):
        """
        Test adding a project to the portfolio using AI-generated content.

        Verifies that projects can be added from AI analysis of a project JSON file,
        with mocked AI resume generation and JSON parsing to simulate the AI workflow.

        Args:
            self: The test case instance
            mock_orjson: Mocked orjson.loads function for parsing project JSON
            mock_resume: Mocked GenerateProjectResume class for AI content generation

        Returns:
            None: Asserts pass if AI-generated project is successfully added
        """
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

    def test_update_portfolio_contact(self):
        """
        Test updating contact information in the portfolio.

        Verifies that contact fields (email, phone, location, website, name)
        can be updated individually or together, and that only non-None fields
        are modified.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if contact fields are updated correctly
        """
        portfolio = Create_Portfolio_RenderCV(auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate_portfolio(name="Test User")
        portfolio.load_Protfolio_starter_file()

        # Test updating single field
        result = portfolio.update_portfolio_contact(email="new@email.com")
        self.assertEqual(result, "Successfully updated: email")
        self.assertEqual(portfolio.data['cv']['email'], "new@email.com")

        # Test updating multiple fields
        result = portfolio.update_portfolio_contact(
            phone="+1 555 123 4567",
            location="New York, NY"
        )
        self.assertEqual(result, "Successfully updated: phone, location")
        self.assertEqual(portfolio.data['cv']['phone'], "+1 555 123 4567")
        self.assertEqual(portfolio.data['cv']['location'], "New York, NY")

        # Test no fields updated
        result = portfolio.update_portfolio_contact()
        self.assertEqual(result, "No fields updated")


if __name__ == '__main__':
    unittest.main()