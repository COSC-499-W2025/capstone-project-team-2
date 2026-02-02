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
    """Test suite for the RenderCVDocument class with portfolio document type."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_loaded_portfolio(self):
        """Create a portfolio instance with starter file generated and loaded."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()
        return portfolio

    # ============== CORE TESTS ==============

    def test_generate_load_and_save(self):
        """Test portfolio generation, file creation, loading, and error handling."""
        portfolio = RenderCVDocument(doc_type='portfolio')
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.name = "Test_User"

        # Generate and load
        self.assertEqual(portfolio.generate(name="Test User"), "Success")
        self.assertTrue(portfolio.yaml_file.exists())
        data = portfolio.load()
        self.assertIn('cv', data)

        # Test malformed YAML file without 'cv' key
        malformed_file = Path(self.test_dir) / "Malformed_Portfolio_CV.yaml"
        malformed_file.write_text("design:\n  theme: sb2nov\n")
        portfolio2 = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio2.yaml_file = malformed_file
        portfolio2.name = "Malformed"
        with self.assertRaises(ValueError) as context:
            portfolio2.load()
        self.assertIn("missing required 'cv' key", str(context.exception))

    # ============== CONNECTION TESTS ==============

    def test_connections_crud(self):
        """Test add, modify, remove, and get connections."""
        portfolio = self.create_loaded_portfolio()

        # Add success
        self.assertEqual(portfolio.add_connection(Connections(network="Twitter", username="test")), "Successfully added: Twitter")

        # Add duplicate rejected
        self.assertEqual(portfolio.add_connection(Connections(network="LinkedIn", username="newuser")), "Connection 'LinkedIn' already exists")

        # Add empty network rejected
        self.assertEqual(portfolio.add_connection(Connections(network="", username="testuser")), "Network name cannot be empty")
        self.assertEqual(portfolio.add_connection(Connections(network="   ", username="testuser")), "Network name cannot be empty")

        # Modify success
        self.assertEqual(portfolio.modify_connection("LinkedIn", "newusername"), "Successfully updated: LinkedIn")
        connection = next(c for c in portfolio.current_connections if c['network'] == 'LinkedIn')
        self.assertEqual(connection['username'], "newusername")

        # Modify not found
        self.assertEqual(portfolio.modify_connection("NonExistent", "username"), "Connection 'NonExistent' not found")

        # Get connections
        connections = portfolio.get_connections()
        self.assertIsInstance(connections, list)
        self.assertTrue(len(connections) > 0)
        self.assertTrue(all('network' in c for c in connections))

        # Remove success
        initial_count = len(portfolio.current_connections)
        self.assertEqual(portfolio.remove_connection("LinkedIn"), "Successfully deleted: LinkedIn")
        self.assertEqual(len(portfolio.current_connections), initial_count - 1)

        # Remove not found
        self.assertEqual(portfolio.remove_connection("NonExistent"), "Connection 'NonExistent' not found")

    # ============== PROJECT TESTS ==============

    def test_projects_crud(self):
        """Test add, modify, remove, get, count, has, and clear projects."""
        portfolio = self.create_loaded_portfolio()

        # Add success
        self.assertIn("Successfully added", portfolio.add_project(Project(name="New Project", summary="Test")))

        # Add duplicate rejected
        self.assertEqual(portfolio.add_project(Project(name="New Project", summary="Different")), "Project 'New Project' already exists")

        # Add empty name rejected
        self.assertEqual(portfolio.add_project(Project(name="", summary="Test")), "Project name cannot be empty")
        self.assertEqual(portfolio.add_project(Project(name="   ", summary="Test")), "Project name cannot be empty")

        # Get projects
        projects = portfolio.get_projects()
        self.assertIsInstance(projects, list)
        self.assertTrue(len(projects) > 0)

        # Count and has projects
        self.assertEqual(portfolio.count_projects(), 2)  # Template + New Project
        self.assertTrue(portfolio.has_projects())

        # Modify success
        self.assertEqual(portfolio.modify_project("Project Name", "summary", "Updated summary"), "Successfully modified summary")
        project = next(p for p in portfolio.current_projects if p['name'] == 'Project Name')
        self.assertEqual(project['summary'], "Updated summary")

        # Modify not found
        self.assertEqual(portfolio.modify_project("NonExistent", "summary", "Test"), "Project 'NonExistent' not found")

        # Modify invalid field
        self.assertIn("Invalid field", portfolio.modify_project("Project Name", "invalid_field", "Test"))

        # Remove success
        initial_count = len(portfolio.current_projects)
        self.assertIn("Successfully deleted", portfolio.remove_project("Project Name"))
        self.assertEqual(len(portfolio.current_projects), initial_count - 1)

        # Remove not found
        self.assertEqual(portfolio.remove_project("NonExistent"), "Project 'NonExistent' not found")

        # Clear projects

        portfolio.add_project(Project(name="Another Project", summary="Test"))
        count = len(portfolio.current_projects)
        result = portfolio.clear_projects()
        self.assertIn(f"Successfully cleared {count}", result)
        self.assertEqual(len(portfolio.current_projects), 0)
        self.assertFalse(portfolio.has_projects())

        # Clear when empty
        self.assertEqual(portfolio.clear_projects(), "No projects to clear")

    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.GenerateProjectResume')
    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.orjson.loads')
    def test_add_project_from_ai(self, mock_orjson, mock_resume):
        """Test adding a project using AI-generated content."""
        portfolio = self.create_loaded_portfolio()

        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_resume.return_value.generate.return_value = MagicMock(
            project_title="AI Project", one_sentence_summary="Summary", tech_stack="Python", key_responsibilities=["Task"])

        with patch('builtins.open', mock_open(read_data=b'{}')):
            result = portfolio.add_project_from_ai("project.json")
        self.assertIn("AI Project", result)

    # ============== SKILLS TESTS ==============

    def test_skills_crud(self):
        """Test add, modify, remove, get, count, has, and clear skills."""
        portfolio = self.create_loaded_portfolio()

        # Add success
        self.assertEqual(portfolio.add_skills(Skills(label="Databases", details="PostgreSQL, MongoDB")), "Successfully added skills")
        self.assertTrue(any(s['label'] == 'Databases' for s in portfolio.current_skills))

        # Add duplicate rejected
        self.assertEqual(portfolio.add_skills(Skills(label="Languages", details="Go, Rust")), "Duplicate skill label")

        # Add empty label rejected
        self.assertEqual(portfolio.add_skills(Skills(label="", details="Some skills")), "Skill label cannot be empty")
        self.assertEqual(portfolio.add_skills(Skills(label="   ", details="Some skills")), "Skill label cannot be empty")

        # Get skills
        skills = portfolio.get_skills()
        self.assertIsInstance(skills, list)
        self.assertTrue(len(skills) > 0)
        self.assertTrue(all('label' in s and 'details' in s for s in skills))

        # Count and has skills
        self.assertEqual(portfolio.count_skills(), 4)  # Template 3 + Databases
        self.assertTrue(portfolio.has_skills())

        # Modify success
        self.assertEqual(portfolio.modify_skill("Languages", "Python, Go, Rust"), "Successfully updated skill 'Languages'")
        skill = next(s for s in portfolio.current_skills if s['label'] == 'Languages')
        self.assertEqual(skill['details'], "Python, Go, Rust")

        # Modify not found
        self.assertEqual(portfolio.modify_skill("NonExistent", "Some details"), "Skill 'NonExistent' not found")

        # Remove success
        initial_count = len(portfolio.current_skills)
        self.assertEqual(portfolio.remove_skill("Languages"), "Successfully deleted skill")
        self.assertEqual(len(portfolio.current_skills), initial_count - 1)

        # Remove not found
        self.assertEqual(portfolio.remove_skill("NonExistent"), "Skill 'NonExistent' not found")

        # Clear skills
        count = len(portfolio.current_skills)
        result = portfolio.clear_skills()
        self.assertIn(f"Successfully cleared {count}", result)
        self.assertEqual(len(portfolio.current_skills), 0)
        self.assertFalse(portfolio.has_skills())

        # Clear when empty
        self.assertEqual(portfolio.clear_skills(), "No skills to clear")

    # ============== SUMMARY TESTS ==============

    def test_summary_crud(self):
        """Test update and get summary."""
        portfolio = self.create_loaded_portfolio()

        # Get default summary
        summary = portfolio.get_summary()
        self.assertIn("A brief summary about yourself", summary)

        # Update summary
        self.assertEqual(portfolio.update_summary("My new summary."), "Summary updated successfully")
        self.assertEqual(portfolio.get_summary(), "My new summary.")

        # Get summary when empty
        portfolio.summary = []
        self.assertEqual(portfolio.get_summary(), "")

    # ============== CONTACT & THEME TESTS ==============

    def test_contact_crud(self):
        """Test update and get contact information."""
        portfolio = self.create_loaded_portfolio()

        # Update single field
        result = portfolio.update_contact(email="new@email.com")
        self.assertIs(result, portfolio)  # Returns self for chaining
        self.assertEqual(portfolio.data['cv']['email'], "new@email.com")

        # Update multiple fields
        portfolio.update_contact(phone="+1 555 123 4567", location="New York, NY")
        self.assertEqual(portfolio.data['cv']['phone'], "+1 555 123 4567")
        self.assertEqual(portfolio.data['cv']['location'], "New York, NY")

        # Empty string should not overwrite
        portfolio.update_contact(email="", phone="   ")
        self.assertEqual(portfolio.data['cv']['email'], "new@email.com")
        self.assertEqual(portfolio.data['cv']['phone'], "+1 555 123 4567")

        # Get contact info
        contact = portfolio.get_contact_info()
        self.assertIsInstance(contact, dict)
        self.assertIn('name', contact)
        self.assertIn('email', contact)
        self.assertIn('phone', contact)
        self.assertIn('location', contact)
        self.assertIn('website', contact)

    def test_theme_crud(self):
        """Test update and get theme."""
        portfolio = self.create_loaded_portfolio()

        # Get default theme
        self.assertEqual(portfolio.get_theme(), "sb2nov")

        # Update theme
        result = portfolio.update_theme("classic")
        self.assertIn("Successfully updated", result)
        self.assertEqual(portfolio.get_theme(), "classic")

        # Invalid theme
        with self.assertRaises(ValueError) as context:
            portfolio.update_theme("invalid_theme")
        self.assertIn("Invalid theme", str(context.exception))


if __name__ == '__main__':
    unittest.main()