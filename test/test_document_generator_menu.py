"""
Test suite for document_generator_menu.py CLI functions.

Tests the CRUD operations for connections and projects
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
    RenderCVDocument, Project, Connections, Education, Skills
)
from src.cli.document_generator_menu import (
    _add_connection,
    _manage_connections,
    _manage_education,
    _manage_skills,
    _add_project_manually,
    _add_project_from_ai,
    _modify_project,
    _add_education,
    _add_skills,
    _render_document,
    _view_document,
    document_generator_menu,
)


class TestDocumentGeneratorMenu(unittest.TestCase):
    """
    Test suite for document_generator_menu CLI functions.

    Tests CRUD operations for connections and projects
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

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_manage_connections_add(self, mock_stdout, mock_input):
        """
        Test the consolidated manage connections menu - add flow.

        Verifies the unified connection management menu can add new connections.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts connection is added successfully
        """
        # Add a connection via manage menu: 'a' to add, network, username, '0' to exit
        # _add_connection asks for network then username
        mock_input.side_effect = ["a", "LinkedIn", "testlinkedin", "0"]
        _manage_connections(self.doc)

        self.assertIn("[SUCCESS]", mock_stdout.getvalue())
        connections = self.doc.data['cv'].get('social_networks', [])
        linkedin = next((c for c in connections if c['network'] == 'LinkedIn'), None)
        self.assertIsNotNone(linkedin)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_manage_connections_delete(self, mock_stdout, mock_input):
        """
        Test the consolidated manage connections menu - delete flow.

        Verifies the unified connection management menu can delete connections.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts connection is deleted successfully
        """
        # First add a connection
        self.doc.add_connection(Connections(network="GitHub", username="testgithub"))

        # Delete via manage menu: 'd' to delete, '1' to select first, 'y' to confirm, '0' to exit
        mock_input.side_effect = ["d", "1", "y", "0"]
        _manage_connections(self.doc)

        self.assertIn("deleted", mock_stdout.getvalue().lower())

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_render_document_pdf_default(self, mock_stdout, mock_input):
        """
        Test rendering document with default PDF format selection.

        Ensures render_outputs is invoked with the default format when
        the user presses Enter at the format prompt.
        """
        mock_doc = MagicMock()
        mock_doc.render_outputs.return_value = (
            "successfully rendered",
            {"pdf": [Path("rendercv_output/Test_Resume.pdf")]}
        )
        mock_input.side_effect = ["", "n"]

        _render_document(mock_doc)

        mock_doc.render_outputs.assert_called_once_with(["pdf"])
        self.assertIn("PDF generated at", mock_stdout.getvalue())

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_manage_education_add(self, mock_stdout, mock_input):
        """
        Test the consolidated manage education menu - add flow.

        Verifies the unified education management menu can add new entries.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts education entry is added successfully
        """
        # Add education: 'a' to add, institution, area, degree, location, dates, highlights, '0' to exit
        mock_input.side_effect = [
            "a",  # add action
            "Test University",  # institution
            "Computer Science",  # area
            "BS",  # degree
            "City, State",  # location
            "2020-09",  # start date
            "2024-05",  # end date
            "Dean's List",  # highlight 1
            "",  # end highlights
            "0"  # exit menu
        ]
        _manage_education(self.doc)

        self.assertIn("[SUCCESS]", mock_stdout.getvalue())
        education = self.doc.data['cv']['sections'].get('education', [])
        entry = next((e for e in education if e.get('institution') == 'Test University'), None)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['area'], 'Computer Science')

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_manage_education_delete(self, mock_stdout, mock_input):
        """
        Test the consolidated manage education menu - delete flow.

        Verifies the unified education management menu can delete entries.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts education entry is deleted successfully
        """
        # First add an education entry
        edu = Education(
            institution="Delete University",
            area="Testing",
            degree="PhD",
            start_date="2020-01",
            end_date="2024-01"
        )
        self.doc.add_education(edu)

        # Delete via manage menu: 'd' to delete, '1' to select, 'y' to confirm, '0' to exit
        mock_input.side_effect = ["d", "1", "y", "0"]
        _manage_education(self.doc)

        self.assertIn("deleted", mock_stdout.getvalue().lower())

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_manage_skills_add(self, mock_stdout, mock_input):
        """
        Test the consolidated manage skills menu - add flow.

        Verifies the unified skills management menu can add new skill categories.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts skill category is added successfully
        """
        # Add skill: 'a' to add, label, details, '0' to exit
        mock_input.side_effect = [
            "a",  # add action
            "Programming Languages",  # label
            "Python, Java, C++",  # details
            "0"  # exit menu
        ]
        _manage_skills(self.doc)

        self.assertIn("[SUCCESS]", mock_stdout.getvalue())
        skills = self.doc.data['cv']['sections'].get('skills', [])
        skill = next((s for s in skills if s.get('label') == 'Programming Languages'), None)
        self.assertIsNotNone(skill)
        self.assertEqual(skill['details'], 'Python, Java, C++')

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_manage_skills_delete(self, mock_stdout, mock_input):
        """
        Test the consolidated manage skills menu - delete flow.

        Verifies the unified skills management menu can delete skill entries.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts skill entry is deleted successfully
        """
        # First add a skill entry
        skill = Skills(label="Test Skill", details="Some details")
        self.doc.add_skills(skill)

        # Delete via manage menu: 'd' to delete, '1' to select, 'y' to confirm, '0' to exit
        mock_input.side_effect = ["d", "1", "y", "0"]
        _manage_skills(self.doc)

        self.assertIn("deleted", mock_stdout.getvalue().lower())

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_view_document(self, mock_stdout, mock_input):
        """
        Test viewing the full document contents.

        Verifies that the document viewer displays contact info and sections.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate user input

        Returns:
            None: Asserts document content is displayed
        """
        # Press enter to continue after viewing
        mock_input.return_value = ""
        _view_document(self.doc)

        output = mock_stdout.getvalue()
        # Document type (RESUME or PORTFOLIO) should be displayed
        self.assertTrue("RESUME" in output.upper() or "PORTFOLIO" in output.upper())
        self.assertIn("Test", output)  # Name should appear

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('src.cli.document_generator_menu.RenderCVDocument')
    def test_document_generator_menu_create_resume(self, mock_rendercv, mock_stdout, mock_input):
        """
        Test the main document generator menu - create resume flow.

        Verifies the main menu can create a new resume document.

        Args:
            mock_rendercv: Mocked RenderCVDocument class
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts resume creation flow is triggered
        """
        # Setup mock document
        mock_doc = MagicMock()
        mock_doc.doc_type = 'resume'
        mock_doc.name = 'Test_User'
        mock_doc.data = {'cv': {'sections': {}}}
        mock_doc.generate.return_value = "Generated"
        mock_rendercv.return_value = mock_doc

        # Create resume: '1' to create resume, enter name, '0' to save and return, '0' to exit
        mock_input.side_effect = ["1", "Test User", "0", "0"]
        document_generator_menu()

        # Verify RenderCVDocument was called with resume type
        mock_rendercv.assert_called_with(doc_type='resume', auto_save=True)
        mock_doc.generate.assert_called_once()

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('src.cli.document_generator_menu.RenderCVDocument')
    def test_document_generator_menu_create_portfolio(self, mock_rendercv, mock_stdout, mock_input):
        """
        Test the main document generator menu - create portfolio flow.

        Verifies the main menu can create a new portfolio document.

        Args:
            mock_rendercv: Mocked RenderCVDocument class
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts portfolio creation flow is triggered
        """
        # Setup mock document
        mock_doc = MagicMock()
        mock_doc.doc_type = 'portfolio'
        mock_doc.name = 'Test_User'
        mock_doc.data = {'cv': {'sections': {}}}
        mock_doc.generate.return_value = "Generated"
        mock_rendercv.return_value = mock_doc

        # Create portfolio: '2' to create portfolio, enter name, '0' to save and return, '0' to exit
        mock_input.side_effect = ["2", "Test User", "0", "0"]
        document_generator_menu()

        # Verify RenderCVDocument was called with portfolio type
        mock_rendercv.assert_called_with(doc_type='portfolio', auto_save=True)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_document_generator_menu_exit(self, mock_stdout, mock_input):
        """
        Test the main document generator menu - exit flow.

        Verifies the menu exits cleanly when user selects exit option.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate menu navigation

        Returns:
            None: Asserts menu exits without error
        """
        # Exit immediately: '0' to exit
        mock_input.side_effect = ["0"]
        document_generator_menu()

        # Menu should display and exit cleanly
        output = mock_stdout.getvalue()
        self.assertIn("Document Generator", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_document_generator_menu_invalid_option(self, mock_stdout, mock_input):
        """
        Test the main document generator menu - invalid option handling.

        Verifies the menu handles invalid input gracefully.

        Args:
            mock_stdout: Mocked stdout to capture printed output
            mock_input: Mocked input function to simulate invalid input

        Returns:
            None: Asserts error message is displayed for invalid input
        """
        # Invalid option then exit: '9' invalid, '0' to exit
        mock_input.side_effect = ["9", "0"]
        document_generator_menu()

        output = mock_stdout.getvalue()
        self.assertIn("valid option", output.lower())


    @patch('src.cli.document_generator_menu.GenerateResumeAI_Ver2')
    @patch('src.cli.document_generator_menu.runtimeAppContext')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_from_ai_success(self, mock_stdout, mock_input, mock_ctx, mock_gen_cls):
        """
        Test adding a project from AI analysis (Ver2) with valid selection and dates.
        """
        mock_ctx.external_consent = True
        mock_ctx.store.get_all_projects_with_versions.return_value = [
            {"project_name": "MyProject", "total_versions": 2},
        ]

        mock_resume = MagicMock()
        mock_resume.project_title = "MyProject"
        mock_resume.one_sentence_summary = "A great project"
        mock_resume.tech_stack = "Python, Flask"
        mock_resume.key_responsibilities = ["Built API", "Wrote tests"]
        mock_gen_cls.return_value.generate_AI_Resume_entry.return_value = mock_resume

        # Select project 1, enter start date, enter end date
        mock_input.side_effect = ["1", "2024-01", "2024-06"]
        _add_project_from_ai(self.doc)

        output = mock_stdout.getvalue()
        self.assertIn("[SUCCESS]", output)

        projects = self.doc.data['cv']['sections'].get('projects', [])
        proj = next((p for p in projects if p['name'] == 'MyProject'), None)
        self.assertIsNotNone(proj)
        self.assertEqual(proj['start_date'], '2024-01')
        self.assertEqual(proj['end_date'], '2024-06')
        self.assertIn("Python, Flask", proj['summary'])
        self.assertEqual(len(proj['highlights']), 2)

    @patch('src.cli.document_generator_menu.GenerateResumeAI_Ver2')
    @patch('src.cli.document_generator_menu.runtimeAppContext')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_from_ai_no_dates(self, mock_stdout, mock_input, mock_ctx, mock_gen_cls):
        """
        Test adding a project from AI analysis with dates skipped.
        """
        mock_ctx.external_consent = True
        mock_ctx.store.get_all_projects_with_versions.return_value = [
            {"project_name": "SkipDates", "total_versions": 1},
        ]

        mock_resume = MagicMock()
        mock_resume.project_title = "SkipDates"
        mock_resume.one_sentence_summary = "No dates project"
        mock_resume.tech_stack = ""
        mock_resume.key_responsibilities = ["Did stuff"]
        mock_gen_cls.return_value.generate_AI_Resume_entry.return_value = mock_resume

        # Select project 1, skip both dates
        mock_input.side_effect = ["1", "", ""]
        _add_project_from_ai(self.doc)

        projects = self.doc.data['cv']['sections'].get('projects', [])
        proj = next((p for p in projects if p['name'] == 'SkipDates'), None)
        self.assertIsNotNone(proj)
        self.assertIsNone(proj.get('start_date'))
        self.assertIsNone(proj.get('end_date'))

    @patch('src.cli.document_generator_menu.runtimeAppContext')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_from_ai_no_consent(self, mock_stdout, mock_input, mock_ctx):
        """
        Test that AI analysis is blocked when external consent is disabled.
        """
        mock_ctx.external_consent = False
        _add_project_from_ai(self.doc)

        output = mock_stdout.getvalue()
        self.assertIn("External services are disabled", output)

    @patch('src.cli.document_generator_menu.runtimeAppContext')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_from_ai_no_projects(self, mock_stdout, mock_input, mock_ctx):
        """
        Test AI analysis when no projects exist in the database.
        """
        mock_ctx.external_consent = True
        mock_ctx.store.get_all_projects_with_versions.return_value = []
        _add_project_from_ai(self.doc)

        output = mock_stdout.getvalue()
        self.assertIn("No analyzed projects found", output)

    @patch('src.cli.document_generator_menu.runtimeAppContext')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_from_ai_cancel(self, mock_stdout, mock_input, mock_ctx):
        """
        Test cancelling project selection in AI analysis.
        """
        mock_ctx.external_consent = True
        mock_ctx.store.get_all_projects_with_versions.return_value = [
            {"project_name": "Proj1", "total_versions": 1},
        ]
        initial_count = len(self.doc.data['cv']['sections'].get('projects', []))
        mock_input.side_effect = ["0"]
        _add_project_from_ai(self.doc)

        # No new project should have been added
        projects = self.doc.data['cv']['sections'].get('projects', [])
        self.assertEqual(len(projects), initial_count)

    @patch('src.cli.document_generator_menu.runtimeAppContext')
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_project_from_ai_invalid_selection(self, mock_stdout, mock_input, mock_ctx):
        """
        Test invalid selection in AI analysis project list.
        """
        mock_ctx.external_consent = True
        mock_ctx.store.get_all_projects_with_versions.return_value = [
            {"project_name": "Proj1", "total_versions": 1},
        ]
        mock_input.side_effect = ["5"]
        _add_project_from_ai(self.doc)

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR] Invalid selection", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_modify_project_with_dates(self, mock_stdout, mock_input):
        """
        Test modifying a project entry including start and end dates.
        """
        # Add a project first
        self.doc.add_project(Project(
            name="Original",
            summary="Original summary",
            highlights=["Original highlight"]
        ))

        projects = self.doc.data['cv']['sections'].get('projects', [])
        idx = len(projects) - 1
        project = projects[idx]

        # Modify: new name, start date, end date, new summary, don't edit highlights
        mock_input.side_effect = [
            "Updated Name",   # name
            "2023-06",        # start date
            "2024-12",        # end date
            "Updated summary", # summary
            "n",              # don't edit highlights
        ]
        _modify_project(self.doc, idx, project)

        output = mock_stdout.getvalue()
        self.assertIn("[SUCCESS]", output)

        updated = self.doc.data['cv']['sections']['projects'][idx]
        self.assertEqual(updated['name'], 'Updated Name')
        self.assertEqual(updated['start_date'], '2023-06')
        self.assertEqual(updated['end_date'], '2024-12')
        self.assertEqual(updated['summary'], 'Updated summary')
        # Highlights unchanged
        self.assertEqual(updated['highlights'], ['Original highlight'])

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_modify_project_skip_dates(self, mock_stdout, mock_input):
        """
        Test modifying a project while skipping date fields preserves existing values.
        """
        self.doc.add_project(Project(
            name="DateTest",
            start_date="2022-01",
            end_date="2023-01",
            summary="Has dates",
            highlights=["H1"]
        ))

        projects = self.doc.data['cv']['sections'].get('projects', [])
        idx = len(projects) - 1
        project = projects[idx]

        # Skip all fields (press Enter on everything)
        mock_input.side_effect = [
            "",   # keep name
            "",   # keep start date
            "",   # keep end date
            "",   # keep summary
            "n",  # don't edit highlights
        ]
        _modify_project(self.doc, idx, project)

        updated = self.doc.data['cv']['sections']['projects'][idx]
        self.assertEqual(updated['name'], 'DateTest')
        self.assertEqual(updated['start_date'], '2022-01')
        self.assertEqual(updated['end_date'], '2023-01')

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_modify_project_with_highlights(self, mock_stdout, mock_input):
        """
        Test modifying a project including replacing highlights.
        """
        self.doc.add_project(Project(
            name="HighlightTest",
            summary="Test",
            highlights=["Old highlight"]
        ))

        projects = self.doc.data['cv']['sections'].get('projects', [])
        idx = len(projects) - 1
        project = projects[idx]

        mock_input.side_effect = [
            "",              # keep name
            "2024-01",       # add start date
            "2024-12",       # add end date
            "",              # keep summary
            "y",             # edit highlights
            "New highlight 1",
            "New highlight 2",
            "",              # end highlights
        ]
        _modify_project(self.doc, idx, project)

        updated = self.doc.data['cv']['sections']['projects'][idx]
        self.assertEqual(updated['start_date'], '2024-01')
        self.assertEqual(updated['end_date'], '2024-12')
        self.assertEqual(updated['highlights'], ['New highlight 1', 'New highlight 2'])


if __name__ == '__main__':
    unittest.main()
