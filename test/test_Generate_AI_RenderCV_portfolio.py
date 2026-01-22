import unittest
import os
import tempfile
import shutil
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Suppress third-party deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")


class TestPortfolio(unittest.TestCase):
    """
    Test suite for the RenderCVDocument class with portfolio document type.

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
        portfolio = RenderCVDocument(doc_type='portfolio')
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        self.assertEqual(portfolio.generate(name="Test User"), "Success")
        self.assertTrue(portfolio.yaml_file.exists())
        data = portfolio.load()
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
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()
        self.assertEqual(portfolio.add_connection(Connections(network="Twitter", username="test")), "Successfully added: Twitter")
        self.assertIn("Successfully added", portfolio.add_project(Project(name="New Project", summary="Test")))

    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.GenerateProjectResume')
    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.orjson.loads')
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
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_resume.return_value.generate.return_value = MagicMock(
            project_title="AI Project", one_sentence_summary="Summary", tech_stack="Python", key_responsibilities=["Task"])

        m = mock_open(read_data=b'{}')
        with patch('builtins.open', m):
            result = portfolio.add_project_from_ai("project.json")

        self.assertIn("AI Project", result)

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
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        # Test updating single field
        result = portfolio.update_contact(email="new@email.com")
        # update_contact returns self for method chaining
        self.assertIs(result, portfolio)
        self.assertEqual(portfolio.data['cv']['email'], "new@email.com")

        # Test updating multiple fields
        result = portfolio.update_contact(
            phone="+1 555 123 4567",
            location="New York, NY"
        )
        self.assertIs(result, portfolio)
        self.assertEqual(portfolio.data['cv']['phone'], "+1 555 123 4567")
        self.assertEqual(portfolio.data['cv']['location'], "New York, NY")

    def test_update_portfolio_contact_empty_string_ignored(self):
        """
        Test that empty strings do not overwrite existing contact information.

        Verifies that passing empty strings or whitespace-only strings to
        update_contact() does not blank out existing values,
        preventing accidental data loss.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if empty strings are properly ignored
        """
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        # Set initial values
        portfolio.update_contact(email="original@email.com", phone="+1 111 111 1111")
        self.assertEqual(portfolio.data['cv']['email'], "original@email.com")
        self.assertEqual(portfolio.data['cv']['phone'], "+1 111 111 1111")

        # Empty string should not overwrite
        result = portfolio.update_contact(email="", phone="")
        self.assertIs(result, portfolio)
        self.assertEqual(portfolio.data['cv']['email'], "original@email.com")
        self.assertEqual(portfolio.data['cv']['phone'], "+1 111 111 1111")

        # Whitespace-only string should not overwrite
        result = portfolio.update_contact(email="   ", phone="\t\n")
        self.assertIs(result, portfolio)
        self.assertEqual(portfolio.data['cv']['email'], "original@email.com")
        self.assertEqual(portfolio.data['cv']['phone'], "+1 111 111 1111")

    def test_load_portfolio_missing_cv_key_raises_error(self):
        """
        Test that loading a YAML file without 'cv' key raises ValueError.

        Verifies that malformed YAML files missing the required 'cv' key
        are properly detected and raise a clear error message instead of
        a cryptic KeyError.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if ValueError is raised with correct message
        """
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)

        # Create a malformed YAML file without 'cv' key
        malformed_file = Path(self.test_dir) / "Test_User_Portfolio_CV.yaml"
        malformed_file.write_text("design:\n  theme: sb2nov\n")
        portfolio.yaml_file = malformed_file
        portfolio.name = "Test_User"

        with self.assertRaises(ValueError) as context:
            portfolio.load()

        self.assertIn("missing required 'cv' key", str(context.exception))

    def test_add_duplicate_connection_rejected(self):
        """
        Test that adding a duplicate social network connection is rejected.

        Verifies that attempting to add a connection with a network name
        that already exists returns an appropriate error message.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if duplicate connection is properly rejected
        """
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        # LinkedIn already exists in template
        result = portfolio.add_connection(
            Connections(network="LinkedIn", username="newuser")
        )
        self.assertEqual(result, "Connection 'LinkedIn' already exists")

    def test_add_duplicate_project_rejected(self):
        """
        Test that adding a duplicate project is rejected.

        Verifies that attempting to add a project with a name that already
        exists returns an appropriate error message.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if duplicate project is properly rejected
        """
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        # Add a project first
        portfolio.add_project(Project(name="My Project", summary="Test"))

        # Try to add duplicate
        result = portfolio.add_project(Project(name="My Project", summary="Different"))
        self.assertEqual(result, "Project 'My Project' already exists")

    def test_add_connection_empty_network_rejected(self):
        """
        Test that adding a connection with empty network name is rejected.

        Verifies that attempting to add a connection with an empty or
        whitespace-only network name returns an appropriate error message.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if empty network name is properly rejected
        """
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        # Empty string network name
        result = portfolio.add_connection(
            Connections(network="", username="testuser")
        )
        self.assertEqual(result, "Network name cannot be empty")

        # Whitespace-only network name
        result = portfolio.add_connection(
            Connections(network="   ", username="testuser")
        )
        self.assertEqual(result, "Network name cannot be empty")

    def test_add_project_empty_name_rejected(self):
        """
        Test that adding a project with empty name is rejected.

        Verifies that attempting to add a project with an empty or
        whitespace-only name returns an appropriate error message.

        Args:
            self: The test case instance

        Returns:
            None: Asserts pass if empty project name is properly rejected
        """
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"
        portfolio.generate(name="Test User")
        portfolio.load()

        # Empty string project name
        result = portfolio.add_project(Project(name="", summary="Test"))
        self.assertEqual(result, "Project name cannot be empty")

        # Whitespace-only project name
        result = portfolio.add_project(Project(name="   ", summary="Test"))
        self.assertEqual(result, "Project name cannot be empty")


if __name__ == '__main__':
    unittest.main()