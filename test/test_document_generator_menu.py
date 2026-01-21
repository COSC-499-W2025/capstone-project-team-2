"""
Test suite for document_generator_menu.py CLI functions.

Tests the CRUD operations for connections, projects, and theme changes
through the CLI menu interface.
"""

import unittest
import os
import sys
import tempfile
import shutil
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Suppress third-party deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")

# Mock the app_context module before importing document_generator_menu
# This prevents the module-level database connection attempt
mock_app_context = MagicMock()
mock_app_context.AppContext = MagicMock()
mock_app_context.runtimeAppContext = MagicMock()
mock_app_context.create_app_context = MagicMock(return_value=mock_app_context.runtimeAppContext)
sys.modules['src.core.app_context'] = mock_app_context

from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument, Project, Connections
)
from src.cli.document_generator_menu import (
    _add_connection,
    _modify_delete_connections,
    _change_theme,
    _add_project_manually,
)


class TestDocumentGeneratorMenu(unittest.TestCase):
    """
    Test suite for document_generator_menu CLI functions.

    Tests CRUD operations for connections, projects, and theme changes
    through the CLI menu interface using mocked user input.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.

        Creates a temporary directory, initializes a test RenderCVDocument,
        and generates a base document for testing.

        Args:
            None

        Returns:
            None: Sets instance attributes for test_dir, original_cwd, and doc
        """
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create a test document
        self.doc = RenderCVDocument(doc_type='resume', auto_save=False)
        self.doc.cv_files_dir = Path(self.test_dir)
        self.doc.name = "Test_User"
        self.doc.generate(name="Test User")
        self.doc.load()

    def tearDown(self):
        """
        Clean up test fixtures after each test method.

        Restores the original working directory and removes the temporary
        test directory along with all its contents.

        Args:
            None

        Returns:
            None: Cleans up filesystem state created during setUp
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_connection(self, mock_stdout, mock_input):
        """
        Test adding social network connections through the CLI.

        Verifies successful connection addition with valid input and
        proper error handling when required fields are empty.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate user input

        Returns:
            None: Asserts expected behavior for add connection functionality
        """
        # Test successful add
        mock_input.side_effect = ["Twitter", "testuser"]
        _add_connection(self.doc)
        self.assertIn("[SUCCESS]", mock_stdout.getvalue())

        # Verify connection was added
        connections = self.doc.data['cv'].get('social_networks', [])
        twitter = next((c for c in connections if c['network'] == 'Twitter'), None)
        self.assertIsNotNone(twitter)
        self.assertEqual(twitter['username'], 'testuser')

        # Test empty network rejected
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        mock_input.side_effect = [""]
        _add_connection(self.doc)
        self.assertIn("[ERROR]", mock_stdout.getvalue())

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_modify_delete_connections(self, mock_stdout, mock_input):
        """
        Test modifying and deleting social network connections.

        Verifies that existing connections can be modified with new values
        and deleted with confirmation. Tests the full modify/delete workflow.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate user menu selections

        Returns:
            None: Asserts expected behavior for modify and delete operations
        """
        # Add a test connection first
        self.doc.add_connection(Connections(network="Twitter", username="olduser"))
        connections = self.doc.data['cv'].get('social_networks', [])
        idx = next((i for i, c in enumerate(connections) if c['network'] == 'Twitter'), None)

        # Test modify
        mock_input.side_effect = [str(idx + 1), "1", "X", "newuser", "0"]
        _modify_delete_connections(self.doc)
        self.assertIn("[SUCCESS]", mock_stdout.getvalue())

        connections = self.doc.data['cv'].get('social_networks', [])
        x_conn = next((c for c in connections if c['network'] == 'X'), None)
        self.assertIsNotNone(x_conn)
        self.assertEqual(x_conn['username'], 'newuser')

        # Test delete
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        idx = next((i for i, c in enumerate(connections) if c['network'] == 'X'), None)
        mock_input.side_effect = [str(idx + 1), "2", "y", "0"]
        _modify_delete_connections(self.doc)
        self.assertIn("deleted", mock_stdout.getvalue().lower())

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_change_theme(self, mock_stdout, mock_input):
        """
        Test changing the document theme through the CLI.

        Verifies theme change to a new theme shows success, selecting the
        same theme shows info message, and canceling leaves theme unchanged.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate theme selection

        Returns:
            None: Asserts expected behavior for theme change functionality
        """
        # Test change to classic
        mock_input.return_value = "1"
        _change_theme(self.doc)
        self.assertIn("[SUCCESS]", mock_stdout.getvalue())
        self.assertEqual(self.doc.data['design']['theme'], 'classic')

        # Test same theme shows info
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        mock_input.return_value = "1"
        _change_theme(self.doc)
        self.assertIn("[INFO]", mock_stdout.getvalue())

        # Test cancel
        mock_input.return_value = "0"
        _change_theme(self.doc)
        self.assertEqual(self.doc.data['design']['theme'], 'classic')  # unchanged

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_manually(self, mock_stdout, mock_input):
        """
        Test manually adding projects through the CLI.

        Verifies successful project creation with full details including
        name, dates, summary, and highlights. Also tests validation that
        rejects empty project names.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate project details entry

        Returns:
            None: Asserts expected behavior for manual project addition
        """
        # Test full project
        mock_input.side_effect = [
            "Test Project", "2023-01", "2024-06",
            "A test summary", "Feature 1", "Feature 2", ""
        ]
        _add_project_manually(self.doc)
        self.assertIn("[SUCCESS]", mock_stdout.getvalue())

        projects = self.doc.data['cv']['sections'].get('projects', [])
        proj = next((p for p in projects if p['name'] == 'Test Project'), None)
        self.assertIsNotNone(proj)
        self.assertEqual(proj['start_date'], '2023-01')
        self.assertEqual(len(proj['highlights']), 2)

        # Test empty name rejected
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        mock_input.side_effect = [""]
        _add_project_manually(self.doc)
        self.assertIn("[ERROR]", mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()