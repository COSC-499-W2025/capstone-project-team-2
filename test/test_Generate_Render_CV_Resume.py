import unittest
import sys
import os
import gc
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Suppress third-party library warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")

# Import from the unified module
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    Education,
    Connections,
    Project,
    Skills,
    Experience,
    RenderCVDocument,
)


class BaseRenderCVTest(unittest.TestCase):
    """Base class with common setup/teardown for all RenderCV tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        gc.collect()
        self._cleanup_cv_files()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gc.collect()
        self._cleanup_cv_files()

    def _cleanup_cv_files(self):
        """Remove test CV files from the project directory."""
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for pattern in ["Test_User_Resume_CV.yaml", "John_Doe_Resume_CV.yaml", "Named_User_Resume_CV.yaml"]:
            for f in cv_dir.glob(pattern):
                try:
                    f.unlink(missing_ok=True)
                except PermissionError:
                    pass

    def create_loaded_cv(self, auto_save=False):
        """Create a CV instance with starter file generated and loaded."""
        cv = RenderCVDocument(doc_type='resume', auto_save=auto_save)
        cv.cv_files_dir = Path(self.test_dir)
        cv.name = "Test_User"
        cv.generate(name="Test User")
        cv.load()
        return cv


class TestRenderCVDocument(BaseRenderCVTest):
    """Tests for initialization, generation, loading, and saving."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        cv = RenderCVDocument()
        self.assertTrue(cv.auto_save)
        self.assertEqual(cv.chosen_theme, 'sb2nov')
        self.assertEqual(cv.output_dir, Path('rendercv_output'))
        self.assertIsNone(cv.data)
        self.assertEqual(cv.doc_type, 'resume')

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        cv = RenderCVDocument(doc_type='resume', auto_save=False, output_dir='custom_output')
        self.assertFalse(cv.auto_save)
        self.assertEqual(cv.output_dir, Path('custom_output'))

    def test_generate_creates_file_with_name_formatting(self):
        """Test generate creates file and formats name correctly."""
        cv = RenderCVDocument(doc_type='resume')
        cv.cv_files_dir = Path(self.test_dir)
        result = cv.generate(name="John Doe")
        self.assertEqual(result, "Success")
        self.assertEqual(cv.name, "John_Doe")
        self.assertTrue(cv.yaml_file.exists())
        self.assertTrue(str(cv.yaml_file).endswith("John_Doe_Resume_CV.yaml"))

    def test_generate_skip_and_overwrite(self):
        """Test skip existing and overwrite behavior."""
        cv = RenderCVDocument(doc_type='resume')
        cv.cv_files_dir = Path(self.test_dir)
        cv.generate(name="Test User")

        # Skip existing
        result = cv.generate(name="Test User", overwrite=False)
        self.assertEqual(result, "Skipping generation")

        # Overwrite existing
        del cv
        gc.collect()
        cv2 = RenderCVDocument(doc_type='resume')
        cv2.cv_files_dir = Path(self.test_dir)
        result = cv2.generate(name="Test User", overwrite=True)
        self.assertEqual(result, "Success")

    def test_load_success_and_populates_data(self):
        """Test loading populates data, sections, and summary."""
        cv = RenderCVDocument(doc_type='resume')
        cv.cv_files_dir = Path(self.test_dir)
        cv.generate(name="Test User")
        data = cv.load()

        self.assertIsNotNone(data)
        self.assertIn('cv', data)
        self.assertIn('sections', data['cv'])
        self.assertIsNotNone(cv.sections)
        self.assertIsInstance(cv.summary, list)

    def test_load_file_not_found(self):
        """Test FileNotFoundError when file doesn't exist."""
        cv = RenderCVDocument(doc_type='resume')
        cv.yaml_file = Path("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            cv.load()

    def test_load_with_name_parameter(self):
        """Test loading by name without calling generate first."""
        cv1 = RenderCVDocument(doc_type='resume')
        cv1.cv_files_dir = Path(self.test_dir)
        cv1.generate(name="Named User")

        cv2 = RenderCVDocument(doc_type='resume')
        cv2.cv_files_dir = Path(self.test_dir)
        data = cv2.load(name="Named User")
        self.assertIsNotNone(data)
        self.assertEqual(cv2.name, "Named_User")

    def test_save_operations(self):
        """Test save without data, with data, and custom filename."""
        # Without data
        cv = RenderCVDocument(doc_type='resume')
        with self.assertRaises(ValueError) as context:
            cv.save()
        self.assertEqual(str(context.exception), "No data loaded")

        # With data
        cv = self.create_loaded_cv(auto_save=False)
        output_file = cv.save()
        self.assertTrue(output_file.exists())

        # Custom filename
        output_file = cv.save(filename="custom_cv.yaml")
        self.assertEqual(output_file, Path("custom_cv.yaml"))


class TestRequiresDataDecorator(BaseRenderCVTest):
    """Consolidated tests for @requires_data decorator - all methods that need loaded data."""

    def test_operations_without_data_raise_error(self):
        """Test that all data-requiring operations raise ValueError when data not loaded."""
        cv = RenderCVDocument(doc_type='resume')

        operations = [
            (cv.add_education, (Education(institution="Test", area="Test"),)),
            (cv.remove_education, ("Test",)),
            (cv.add_experience, (Experience(company="Test"),)),
            (cv.remove_experience, ("Test",)),
            (cv.add_project, (Project(name="Test"),)),
            (cv.remove_project, ("Test",)),
            (cv.modify_project, ("Test", "summary", "value")),
            (cv.add_skills, (Skills(label="Test", details="Test"),)),
            (cv.remove_skill, ("Test",)),
            (cv.add_connection, (Connections(network="Test", username="test"),)),
            (cv.modify_connection, ("Test", "newuser")),
            (cv.remove_connection, ("Test",)),
            (cv.update_contact, (), {"email": "test@test.com"}),
            (cv.remove_section, (0,)),
        ]

        for operation in operations:
            if len(operation) == 3:
                func, args, kwargs = operation
            else:
                func, args = operation
                kwargs = {}
            with self.assertRaises(ValueError, msg=f"{func.__name__} should raise ValueError"):
                func(*args, **kwargs)


class TestRenderCVDocumentEducation(BaseRenderCVTest):
    """Tests for education-related methods."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_add_education_success_and_duplicate(self):
        """Test adding education and duplicate detection."""
        edu = Education(institution="New University", area="Physics", degree="MS")
        result = self.cv.add_education(edu)
        self.assertEqual(result, "Successfully added education")

        # Duplicate
        edu = Education(institution="University Name", area="Physics")
        result = self.cv.add_education(edu)
        self.assertEqual(result, "Duplicate education entry")

    def test_remove_education(self):
        """Test removing education - success, not found, and no section."""
        result = self.cv.remove_education("University Name")
        self.assertEqual(result, "Successfully deleted education")

        result = self.cv.remove_education("Nonexistent University")
        self.assertIn("not found", result)

        self.cv.current_education = []
        result = self.cv.remove_education("Test")
        self.assertEqual(result, "No education to delete")


class TestRenderCVDocumentExperience(BaseRenderCVTest):
    """Tests for experience-related methods."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_add_experience_success_and_validation(self):
        """Test adding experience and empty company validation."""
        exp = Experience(
            company="New Company",
            position="Software Engineer",
            start_date="2023-01",
            end_date="2023-12",
            location="Remote",
            highlights=["Built features", "Fixed bugs"]
        )
        result = self.cv.add_experience(exp)
        self.assertEqual(result, "Successfully added experience")

        # Empty company rejected
        exp = Experience(company="", position="Developer")
        result = self.cv.add_experience(exp)
        self.assertEqual(result, "Company name cannot be empty")

    def test_remove_experience(self):
        """Test removing experience - success, not found, and no section."""
        result = self.cv.remove_experience("Company Name")
        self.assertEqual(result, "Successfully removed experience")

        result = self.cv.remove_experience("Nonexistent Company")
        self.assertIn("not found", result)

        self.cv.current_experience = []
        result = self.cv.remove_experience("Test Company")
        self.assertEqual(result, "No experience to delete")


class TestRenderCVDocumentProjects(BaseRenderCVTest):
    """Tests for project-related methods."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_add_project_success_and_duplicate(self):
        """Test adding project and duplicate detection."""
        proj = Project(name="New Project", summary="A new project")
        result = self.cv.add_project(proj)
        self.assertIn("Successfully added", result)

        proj = Project(name="Project Name")
        result = self.cv.add_project(proj)
        self.assertIn("already exists", result)

    def test_remove_project(self):
        """Test removing project - success, not found, and no section."""
        result = self.cv.remove_project("Project Name")
        self.assertIn("Successfully deleted", result)

        result = self.cv.remove_project("Nonexistent Project")
        self.assertIn("not found", result)

        self.cv.current_projects = []
        result = self.cv.remove_project("Test")
        self.assertEqual(result, "No projects to delete")

    def test_modify_project(self):
        """Test modifying project - success, invalid field, not found."""
        result = self.cv.modify_project("Project Name", "summary", "New summary")
        self.assertIn("Successfully modified", result)

        result = self.cv.modify_project("Project Name", "invalid_field", "value")
        self.assertIn("Invalid field", result)

        result = self.cv.modify_project("Nonexistent", "summary", "value")
        self.assertIn("not found", result)


class TestAddProjectFromAI(BaseRenderCVTest):
    """Tests for AI-powered project generation."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_add_project_from_ai_without_data_raises_error(self):
        """Test that adding project from AI without loaded data raises ValueError."""
        cv = RenderCVDocument(doc_type='resume')
        with self.assertRaises(ValueError) as context:
            cv.add_project_from_ai("some_path.json")
        self.assertIn("No data loaded", str(context.exception))

    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.orjson.loads')
    def test_add_project_from_ai_success_with_tech_stack(self, mock_orjson, mock_open, mock_generate_resume):
        """Test successfully adding a project with tech stack in summary."""
        mock_orjson.return_value = {'project_root': '/fake/project/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "AI Generated Project"
        mock_ai_resume.one_sentence_summary = "An amazing AI project"
        mock_ai_resume.tech_stack = "Python, TensorFlow"
        mock_ai_resume.key_responsibilities = ["Built ML models", "Deployed to production"]
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        result = self.cv.add_project_from_ai("project_insight.json")

        self.assertIn("AI Generated Project", result)
        mock_generate_resume.assert_called_once_with('/fake/project/path')

        added_project = next(
            (p for p in self.cv.current_projects if p['name'] == "AI Generated Project"), None
        )
        self.assertIsNotNone(added_project)
        self.assertIn("Tech stack: Python, TensorFlow", added_project['summary'])
        self.assertEqual(added_project['highlights'], ["Built ML models", "Deployed to production"])

    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.orjson.loads')
    def test_add_project_from_ai_without_tech_stack(self, mock_orjson, mock_open, mock_generate_resume):
        """Test adding project when tech_stack is empty."""
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "Simple Project"
        mock_ai_resume.one_sentence_summary = "A simple project"
        mock_ai_resume.tech_stack = ""
        mock_ai_resume.key_responsibilities = ["Did something"]
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        self.cv.add_project_from_ai("project.json")

        added_project = next(
            (p for p in self.cv.current_projects if p['name'] == "Simple Project"), None
        )
        self.assertIsNotNone(added_project)
        self.assertEqual(added_project['summary'], "A simple project")
        self.assertNotIn("Tech stack", added_project['summary'])

    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.orjson.loads')
    def test_add_project_from_ai_duplicate_rejected(self, mock_orjson, mock_open, mock_generate_resume):
        """Test that duplicate AI-generated projects are rejected."""
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "Project Name"
        mock_ai_resume.one_sentence_summary = "Summary"
        mock_ai_resume.tech_stack = ""
        mock_ai_resume.key_responsibilities = []
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        result = self.cv.add_project_from_ai("project.json")
        self.assertIn("already exists", result)

    def test_add_project_from_ai_file_not_found(self):
        """Test FileNotFoundError when project file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            self.cv.add_project_from_ai("nonexistent_file.json")


class TestRenderCVDocumentSkills(BaseRenderCVTest):
    """Tests for skill-related methods."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_add_skills_success_duplicate_and_empty(self):
        """Test adding skills - success, duplicate, and empty label."""
        skill = Skills(label="Testing", details="Unit testing, Integration testing")
        result = self.cv.add_skills(skill)
        self.assertEqual(result, "Successfully added skills")

        skill = Skills(label="Languages", details="Python, Java")
        result = self.cv.add_skills(skill)
        self.assertEqual(result, "Duplicate skill label")

        skill = Skills(label="", details="Some details")
        result = self.cv.add_skills(skill)
        self.assertEqual(result, "Skill label cannot be empty")

    def test_remove_skill(self):
        """Test removing skill - success, not found, and no section."""
        result = self.cv.remove_skill("Languages")
        self.assertEqual(result, "Successfully deleted skill")

        result = self.cv.remove_skill("Nonexistent Skill")
        self.assertIn("not found", result)

        self.cv.current_skills = []
        result = self.cv.remove_skill("Languages")
        self.assertEqual(result, "No skills to delete")


class TestRenderCVDocumentContact(BaseRenderCVTest):
    """Tests for contact-related methods."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_update_contact_all_fields(self):
        """Test updating all contact fields and method chaining."""
        result = self.cv.update_contact(
            email="test@test.com",
            phone="+1 111 222 3333",
            location="Boston, MA",
            website="https://newsite.com",
            name="New Name"
        )

        self.assertEqual(self.cv.data['cv']['email'], "test@test.com")
        self.assertEqual(self.cv.data['cv']['phone'], "+1 111 222 3333")
        self.assertEqual(self.cv.data['cv']['location'], "Boston, MA")
        self.assertEqual(self.cv.data['cv']['website'], "https://newsite.com")
        self.assertEqual(self.cv.data['cv']['name'], "New Name")
        self.assertIs(result, self.cv)  # Returns self for chaining


class TestRenderCVDocumentConnections(BaseRenderCVTest):
    """Tests for connection-related methods."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_add_connection_success_and_duplicate(self):
        """Test adding connection and duplicate detection."""
        conn = Connections(network="Twitter", username="testuser")
        result = self.cv.add_connection(conn)
        self.assertEqual(result, "Successfully added: Twitter")

        conn = Connections(network="LinkedIn", username="testuser")
        result = self.cv.add_connection(conn)
        self.assertIn("already exists", result)

    def test_modify_connection(self):
        """Test modifying connection - success and not found."""
        result = self.cv.modify_connection("LinkedIn", "new_linkedin_user")
        self.assertIn("Successfully updated", result)
        conn = next((c for c in self.cv.current_connections if c.get('network') == 'LinkedIn'), None)
        self.assertEqual(conn['username'], "new_linkedin_user")

        result = self.cv.modify_connection("Twitter", "testuser")
        self.assertIn("not found", result)

    def test_remove_connection(self):
        """Test removing connection - success, not found, and no connections."""
        result = self.cv.remove_connection("LinkedIn")
        self.assertIn("Successfully deleted", result)

        result = self.cv.remove_connection("Twitter")
        self.assertIn("not found", result)

        self.cv.current_connections = []
        result = self.cv.remove_connection("LinkedIn")
        self.assertEqual(result, "No connections to delete")


class TestRenderCVDocumentAutoSave(BaseRenderCVTest):
    """Tests for auto-save functionality."""

    def test_auto_save_behavior(self):
        """Test auto_save triggers or skips save based on setting."""
        # Auto-save enabled
        cv = RenderCVDocument(doc_type='resume', auto_save=True)
        cv.cv_files_dir = Path(self.test_dir)
        cv.generate(name="Test User")
        cv.load()

        with patch.object(cv, 'save') as mock_save:
            cv.add_education(Education(institution="Auto Save Test", area="Testing"))
            mock_save.assert_called()

        # Auto-save disabled
        cv2 = RenderCVDocument(doc_type='resume', auto_save=False)
        cv2.cv_files_dir = Path(self.test_dir)
        cv2.name = "Test_User2"
        cv2.generate(name="Test User2")
        cv2.load()

        with patch.object(cv2, 'save') as mock_save:
            cv2.add_education(Education(institution="No Auto Save Test", area="Testing"))
            mock_save.assert_not_called()


class TestRenderCVDocumentRender(BaseRenderCVTest):
    """Tests for render functionality."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_render_file_not_found(self):
        """Test render raises error when file doesn't exist."""
        cv = RenderCVDocument(doc_type='resume')
        cv.yaml_file = Path("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            cv.render()

    @patch('subprocess.run')
    def test_render_calls_subprocess(self, mock_run):
        """Test render calls subprocess with correct arguments."""
        mock_run.return_value = MagicMock(returncode=1)
        self.cv.render()
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn('rendercv', call_args[0][0])
        self.assertIn('render', call_args[0][0])


class TestThemes(BaseRenderCVTest):
    """Tests for theme functionality."""

    def setUp(self):
        super().setUp()
        self.cv = self.create_loaded_cv()

    def test_themes(self):
        """Test available themes, default theme, and theme updates."""
        cv = RenderCVDocument(doc_type='resume')
        expected_themes = ['classic', 'engineeringclassic', 'engineeringresumes', 'moderncv', 'sb2nov']
        for theme in expected_themes:
            self.assertIn(theme, cv.THEMES)
        self.assertEqual(cv.chosen_theme, 'sb2nov')

        result = self.cv.update_theme('classic')
        self.assertIn("Successfully updated", result)
        self.assertEqual(self.cv.data['design']['theme'], 'classic')

        with self.assertRaises(ValueError):
            self.cv.update_theme('invalid_theme')


class TestPortfolioDocType(BaseRenderCVTest):
    """Tests for portfolio document type restrictions."""

    def test_resume_only_methods_raise_error_for_portfolio(self):
        """Test that resume-only methods raise ValueError for portfolio doc type."""
        portfolio = RenderCVDocument(doc_type='portfolio', auto_save=False)
        portfolio.cv_files_dir = Path(self.test_dir)
        portfolio.generate(name="Test User")
        portfolio.load()

        with self.assertRaises(ValueError) as context:
            portfolio.add_education(Education(institution="Test", area="Test"))
        self.assertIn("requires document type 'resume'", str(context.exception))

        with self.assertRaises(ValueError):
            portfolio.add_experience(Experience(company="Test"))

        with self.assertRaises(ValueError):
            portfolio.add_skills(Skills(label="Test", details="Test"))


if __name__ == '__main__':
    unittest.main()