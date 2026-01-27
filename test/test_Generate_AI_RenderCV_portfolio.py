import unittest
import os
import tempfile
import shutil
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import RenderCVDocument, Connections, Project, Skills

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

    # ============== SUMMARY TESTS ==============

    def test_update_summary(self):
        """Test updating the summary section."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.update_summary("This is my new professional summary.")
        self.assertEqual(result, "Summary updated successfully")
        self.assertEqual(portfolio.sections['summary'][0], "This is my new professional summary.")

    def test_get_summary(self):
        """Test getting the current summary text."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        # Get the default summary
        summary = portfolio.get_summary()
        self.assertIn("A brief summary about yourself and your professional background.", summary)

        # Update and get new summary
        portfolio.update_summary("My custom summary")
        self.assertEqual(portfolio.get_summary(), "My custom summary")

    def test_get_summary_empty(self):
        """Test getting summary when none exists."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        # Clear summary
        portfolio.summary = []
        result = portfolio.get_summary()
        self.assertEqual(result, "")

    # ============== SKILLS TESTS ==============

    def test_add_skills(self):
        """Test adding a new skill category."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.add_skills(Skills(label="Databases", details="PostgreSQL, MongoDB, Redis"))
        self.assertEqual(result, "Successfully added skills")
        self.assertTrue(any(s['label'] == 'Databases' for s in portfolio.current_skills))

    def test_add_skills_duplicate_rejected(self):
        """Test that adding a duplicate skill label is rejected."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        # Languages already exists in template
        result = portfolio.add_skills(Skills(label="Languages", details="Go, Rust"))
        self.assertEqual(result, "Duplicate skill label")

    def test_add_skills_empty_label_rejected(self):
        """Test that adding a skill with empty label is rejected."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.add_skills(Skills(label="", details="Some skills"))
        self.assertEqual(result, "Skill label cannot be empty")

        result = portfolio.add_skills(Skills(label="   ", details="Some skills"))
        self.assertEqual(result, "Skill label cannot be empty")

    def test_modify_skill(self):
        """Test modifying an existing skill category."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.modify_skill("Languages", "Python, Go, Rust, TypeScript")
        self.assertEqual(result, "Successfully updated skill 'Languages'")

        skill = next(s for s in portfolio.current_skills if s['label'] == 'Languages')
        self.assertEqual(skill['details'], "Python, Go, Rust, TypeScript")

    def test_modify_skill_not_found(self):
        """Test modifying a non-existent skill category."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.modify_skill("NonExistent", "Some details")
        self.assertEqual(result, "Skill 'NonExistent' not found")

    def test_remove_skill(self):
        """Test removing a skill category."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        initial_count = len(portfolio.current_skills)
        result = portfolio.remove_skill("Languages")
        self.assertEqual(result, "Successfully deleted skill")
        self.assertEqual(len(portfolio.current_skills), initial_count - 1)
        self.assertFalse(any(s['label'] == 'Languages' for s in portfolio.current_skills))

    def test_remove_skill_not_found(self):
        """Test removing a non-existent skill category."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.remove_skill("NonExistent")
        self.assertEqual(result, "Skill 'NonExistent' not found")

    def test_get_skills(self):
        """Test getting all skill categories."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        skills = portfolio.get_skills()
        self.assertIsInstance(skills, list)
        self.assertTrue(len(skills) > 0)
        self.assertTrue(all('label' in s and 'details' in s for s in skills))

    def test_count_skills(self):
        """Test counting skill categories."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        count = portfolio.count_skills()
        self.assertEqual(count, 3)  # Template has 3 skills

        portfolio.add_skills(Skills(label="New Skill", details="Test"))
        self.assertEqual(portfolio.count_skills(), 4)

    def test_has_skills(self):
        """Test checking if skills exist."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        self.assertTrue(portfolio.has_skills())

        portfolio.clear_skills()
        self.assertFalse(portfolio.has_skills())

    def test_clear_skills(self):
        """Test clearing all skills."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        initial_count = len(portfolio.current_skills)
        result = portfolio.clear_skills()
        self.assertIn(f"Successfully cleared {initial_count}", result)
        self.assertEqual(len(portfolio.current_skills), 0)

    def test_clear_skills_empty(self):
        """Test clearing skills when none exist."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        portfolio.current_skills.clear()
        result = portfolio.clear_skills()
        self.assertEqual(result, "No skills to clear")

    # ============== PROJECT HELPER TESTS ==============

    def test_get_projects(self):
        """Test getting all projects."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        projects = portfolio.get_projects()
        self.assertIsInstance(projects, list)
        self.assertTrue(len(projects) > 0)

    def test_count_projects(self):
        """Test counting projects."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        count = portfolio.count_projects()
        self.assertEqual(count, 1)  # Template has 1 project

        portfolio.add_project(Project(name="New Project", summary="Test"))
        self.assertEqual(portfolio.count_projects(), 2)

    def test_has_projects(self):
        """Test checking if projects exist."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        self.assertTrue(portfolio.has_projects())

        portfolio.clear_projects()
        self.assertFalse(portfolio.has_projects())

    def test_clear_projects(self):
        """Test clearing all projects."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        initial_count = len(portfolio.current_projects)
        result = portfolio.clear_projects()
        self.assertIn(f"Successfully cleared {initial_count}", result)
        self.assertEqual(len(portfolio.current_projects), 0)

    def test_clear_projects_empty(self):
        """Test clearing projects when none exist."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        portfolio.current_projects.clear()
        result = portfolio.clear_projects()
        self.assertEqual(result, "No projects to clear")

    def test_modify_project(self):
        """Test modifying a project field."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        # Modify the template project
        result = portfolio.modify_project("Project Name", "summary", "Updated summary")
        self.assertEqual(result, "Successfully modified summary")

        project = next(p for p in portfolio.current_projects if p['name'] == 'Project Name')
        self.assertEqual(project['summary'], "Updated summary")

    def test_modify_project_not_found(self):
        """Test modifying a non-existent project."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.modify_project("NonExistent", "summary", "Test")
        self.assertEqual(result, "Project 'NonExistent' not found")

    def test_modify_project_invalid_field(self):
        """Test modifying a project with invalid field."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.modify_project("Project Name", "invalid_field", "Test")
        self.assertIn("Invalid field", result)

    def test_remove_project(self):
        """Test removing a project."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        initial_count = len(portfolio.current_projects)
        result = portfolio.remove_project("Project Name")
        self.assertIn("Successfully deleted", result)
        self.assertEqual(len(portfolio.current_projects), initial_count - 1)

    def test_remove_project_not_found(self):
        """Test removing a non-existent project."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.remove_project("NonExistent")
        self.assertEqual(result, "Project 'NonExistent' not found")

    # ============== CONNECTION HELPER TESTS ==============

    def test_modify_connection(self):
        """Test modifying a connection username."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.modify_connection("LinkedIn", "newusername")
        self.assertEqual(result, "Successfully updated: LinkedIn")

        connection = next(c for c in portfolio.current_connections if c['network'] == 'LinkedIn')
        self.assertEqual(connection['username'], "newusername")

    def test_modify_connection_not_found(self):
        """Test modifying a non-existent connection."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.modify_connection("NonExistent", "username")
        self.assertEqual(result, "Connection 'NonExistent' not found")

    def test_remove_connection(self):
        """Test removing a connection."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        initial_count = len(portfolio.current_connections)
        result = portfolio.remove_connection("LinkedIn")
        self.assertEqual(result, "Successfully deleted: LinkedIn")
        self.assertEqual(len(portfolio.current_connections), initial_count - 1)

    def test_remove_connection_not_found(self):
        """Test removing a non-existent connection."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.remove_connection("NonExistent")
        self.assertEqual(result, "Connection 'NonExistent' not found")

    def test_get_connections(self):
        """Test getting all connections."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        connections = portfolio.get_connections()
        self.assertIsInstance(connections, list)
        self.assertTrue(len(connections) > 0)
        self.assertTrue(all('network' in c for c in connections))

    # ============== CONTACT & THEME HELPER TESTS ==============

    def test_get_contact_info(self):
        """Test getting contact information."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        contact = portfolio.get_contact_info()
        self.assertIsInstance(contact, dict)
        self.assertIn('name', contact)
        self.assertIn('email', contact)
        self.assertIn('phone', contact)
        self.assertIn('location', contact)
        self.assertIn('website', contact)

    def test_get_theme(self):
        """Test getting the current theme."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        theme = portfolio.get_theme()
        self.assertEqual(theme, "sb2nov")  # Default theme

    def test_update_theme(self):
        """Test updating the theme."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        result = portfolio.update_theme("classic")
        self.assertIn("Successfully updated", result)
        self.assertEqual(portfolio.get_theme(), "classic")

    def test_update_theme_invalid(self):
        """Test updating with an invalid theme."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        with self.assertRaises(ValueError) as context:
            portfolio.update_theme("invalid_theme")
        self.assertIn("Invalid theme", str(context.exception))


if __name__ == '__main__':
    unittest.main()