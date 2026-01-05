import unittest
import sys
import os
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Suppress third-party library warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")

# Add src directory to path
from src.reporting.Generate_RenderCV_Resume import (
    Education,
    Connections,
    Project,
    Skills,
    Experience,
    create_Render_CV
)


class TestCreateRenderCV(unittest.TestCase):
    """Tests for the create_Render_CV class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Clean up any leftover test files from previous runs
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for pattern in ["Test_User_CV.yaml", "John_Doe_CV.yaml", "Named_User_CV.yaml"]:
            for f in cv_dir.glob(pattern):
                f.unlink(missing_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for pattern in ["Test_User_CV.yaml", "John_Doe_CV.yaml", "Named_User_CV.yaml"]:
            for f in cv_dir.glob(pattern):
                f.unlink(missing_ok=True)

    def test_init_default_values(self):
        """Test initialization with default values."""
        cv = create_Render_CV()
        self.assertTrue(cv.auto_save)
        self.assertEqual(cv.chosen_theme, 'sb2nov')
        self.assertEqual(cv.output_dir, Path('rendercv_output'))
        self.assertIsNone(cv.data)
        self.assertIsNone(cv.yaml_file)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        cv = create_Render_CV(auto_save=False, output_dir='custom_output')
        self.assertFalse(cv.auto_save)
        self.assertEqual(cv.output_dir, Path('custom_output'))

    def test_generate_starter_file_creates_file(self):
        """Test that generate_starter_file creates a YAML file."""
        cv = create_Render_CV()
        result = cv.generate_starter_file(name="Test User")
        self.assertEqual(result, "Success")
        self.assertTrue(cv.yaml_file.exists())

    def test_generate_starter_file_replaces_spaces_in_name(self):
        """Test that spaces in name are replaced with underscores."""
        cv = create_Render_CV()
        cv.generate_starter_file(name="John Doe")
        self.assertEqual(cv.name, "John_Doe")
        # Check that the yaml_file path ends with the correct structure
        self.assertTrue(str(cv.yaml_file).endswith("User_config_files/Generate_render_CV_files/John_Doe_CV.yaml".replace("/", os.sep)))

    def test_generate_starter_file_skip_existing(self):
        """Test that existing file is skipped when overwrite is False."""
        cv = create_Render_CV()
        cv.generate_starter_file(name="Test User")
        result = cv.generate_starter_file(name="Test User", overwrite=False)
        self.assertEqual(result, "Skipping generation")

    def test_generate_starter_file_overwrite_existing(self):
        """Test that existing file is overwritten when overwrite is True."""
        cv = create_Render_CV()
        cv.generate_starter_file(name="Test User")
        result = cv.generate_starter_file(name="Test User", overwrite=True)
        self.assertEqual(result, "Success")

    def test_load_starter_file_success(self):
        """Test loading a starter file successfully."""
        cv = create_Render_CV()
        cv.generate_starter_file(name="Test User")
        data = cv.load_starter_file()
        self.assertIsNotNone(data)
        self.assertIn('cv', data)
        self.assertIn('sections', data['cv'])

    def test_load_starter_file_file_not_found(self):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        cv = create_Render_CV()
        cv.yaml_file = Path("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            cv.load_starter_file()

    def test_load_starter_file_populates_resume_section(self):
        """Test that resume_section is populated after loading."""
        cv = create_Render_CV()
        cv.generate_starter_file(name="Test User")
        cv.load_starter_file()
        self.assertIsNotNone(cv.resume_section)
        self.assertIn('education', cv.resume_section)

    def test_load_starter_file_populates_summary(self):
        """Test that summary is populated after loading."""
        cv = create_Render_CV()
        cv.generate_starter_file(name="Test User")
        cv.load_starter_file()
        self.assertIsNotNone(cv.summary)
        self.assertIsInstance(cv.summary, list)

    def test_load_starter_file_with_name_parameter(self):
        """Test loading a file by name without calling generate_starter_file first."""
        # First create a file
        cv1 = create_Render_CV()
        cv1.generate_starter_file(name="Named User")

        # Now load it using only the name parameter
        cv2 = create_Render_CV()
        data = cv2.load_starter_file(name="Named User")
        self.assertIsNotNone(data)
        self.assertEqual(cv2.name, "Named_User")
        # Check that the yaml_file path ends with the correct structure
        self.assertTrue(str(cv2.yaml_file).endswith("User_config_files/Generate_render_CV_files/Named_User_CV.yaml".replace("/", os.sep)))

    def test_save_without_data_raises_error(self):
        """Test that saving without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError) as context:
            cv.save()
        self.assertEqual(str(context.exception), "No data loaded")

    def test_save_creates_file(self):
        """Test that save creates the YAML file."""
        cv = create_Render_CV(auto_save=False)
        cv.generate_starter_file(name="Test User")
        cv.load_starter_file()
        output_file = cv.save()
        self.assertTrue(output_file.exists())

    def test_save_custom_filename(self):
        """Test saving with a custom filename."""
        cv = create_Render_CV(auto_save=False)
        cv.generate_starter_file(name="Test User")
        cv.load_starter_file()
        output_file = cv.save(filename="custom_cv.yaml")
        self.assertEqual(output_file, Path("custom_cv.yaml"))
        self.assertTrue(output_file.exists())


class TestCreateRenderCVEducation(unittest.TestCase):
    """Tests for education-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_add_education_success(self):
        """Test adding education entry successfully."""
        edu = Education(institution="New University", areaOfStudy="Physics", degree="MS")
        result = self.cv.add_education(edu)
        self.assertEqual(result, "Successfully added education")

    def test_add_education_without_data_raises_error(self):
        """Test that adding education without loaded data raises ValueError."""
        cv = create_Render_CV()
        edu = Education(institution="Test", areaOfStudy="Test")
        with self.assertRaises(ValueError):
            cv.add_education(edu)

    def test_add_education_duplicate_skipped(self):
        """Test that duplicate education entries are skipped."""
        edu = Education(institution="University Name", areaOfStudy="Physics")
        result = self.cv.add_education(edu)
        self.assertEqual(result, "Duplicate education entry")

    def test_add_education_creates_section_if_missing(self):
        """Test that education section is created if it doesn't exist."""
        del self.cv.data['cv']['sections']['education']
        edu = Education(institution="New Uni", areaOfStudy="Math")
        self.cv.add_education(edu)
        self.assertIn('education', self.cv.data['cv']['sections'])

    def test_delete_education_success(self):
        """Test deleting an education entry successfully."""
        result = self.cv.delete_education("University Name")
        self.assertEqual(result, "Successfully deleted education")

    def test_delete_education_not_found(self):
        """Test deleting a non-existent education entry."""
        result = self.cv.delete_education("Nonexistent University")
        self.assertEqual(result, "Education Nonexistent University not found.")

    def test_delete_education_without_data_raises_error(self):
        """Test that deleting education without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.delete_education("Test")

    def test_delete_education_no_education_section(self):
        """Test deleting when no education section exists."""
        del self.cv.data['cv']['sections']['education']
        result = self.cv.delete_education("Test")
        self.assertEqual(result, "No education to be deleted")


class TestCreateRenderCVExperience(unittest.TestCase):
    """Tests for experience-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_add_experience_success(self):
        """Test adding an experience entry successfully."""
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

    def test_add_experience_without_data_raises_error(self):
        """Test that adding experience without loaded data raises ValueError."""
        cv = create_Render_CV()
        exp = Experience(company="Test Company", position="Developer")
        with self.assertRaises(ValueError):
            cv.add_experience(exp)

    def test_add_experience_creates_section_if_missing(self):
        """Test that experience section is created if it doesn't exist."""
        del self.cv.data['cv']['sections']['experience']
        self.cv.current_experience = []
        exp = Experience(company="New Company", position="Developer")
        self.cv.add_experience(exp)
        self.assertIn('experience', self.cv.data['cv']['sections'])

    def test_remove_experience_success(self):
        """Test removing an experience entry successfully."""
        result = self.cv.remove_experience("Company Name")
        self.assertEqual(result, "Successfully removed experience from system")
        # Verify the experience was actually removed
        exp = next((e for e in self.cv.current_experience if e.get('company') == 'Company Name'), None)
        self.assertIsNone(exp)

    def test_remove_experience_without_data_raises_error(self):
        """Test that removing experience without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.remove_experience("Test Company")

    def test_remove_experience_not_found(self):
        """Test removing a non-existent experience entry."""
        result = self.cv.remove_experience("Nonexistent Company")
        self.assertEqual(result, "Experience Nonexistent Company not found.")

    def test_remove_experience_no_experience_section(self):
        """Test removing when no experience section exists."""
        del self.cv.data['cv']['sections']['experience']
        result = self.cv.remove_experience("Test Company")
        self.assertEqual(result, "Experience not found.")

    def test_remove_experience_empty_list(self):
        """Test removing when experience section is empty."""
        self.cv.data['cv']['sections']['experience'] = []
        self.cv.current_experience = []
        result = self.cv.remove_experience("Test Company")
        self.assertEqual(result, "Experience not found.")


class TestCreateRenderCVProjects(unittest.TestCase):
    """Tests for project-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_add_project_success(self):
        """Test adding a project successfully."""
        proj = Project(name="New Project", summary="A new project")
        result = self.cv.add_project(proj)
        self.assertEqual(result, "Successfully added: New Project")

    def test_add_project_without_data_raises_error(self):
        """Test that adding project without loaded data raises ValueError."""
        cv = create_Render_CV()
        proj = Project(name="Test")
        with self.assertRaises(ValueError):
            cv.add_project(proj)

    def test_add_project_duplicate_rejected(self):
        """Test that duplicate projects are rejected."""
        proj = Project(name="Project Name")  # This exists in starter template
        result = self.cv.add_project(proj)
        self.assertIn("already exists", result)

    def test_add_project_creates_section_if_missing(self):
        """Test that projects section is created if it doesn't exist."""
        del self.cv.data['cv']['sections']['projects']
        proj = Project(name="New Project")
        self.cv.add_project(proj)
        self.assertIn('projects', self.cv.data['cv']['sections'])

    def test_delete_project_success(self):
        """Test deleting a project successfully."""
        result = self.cv.delete_project("Project Name")
        self.assertEqual(result, "Successfully deleted: Project Name")

    def test_delete_project_not_found(self):
        """Test deleting a non-existent project."""
        result = self.cv.delete_project("Nonexistent Project")
        self.assertEqual(result, "Project not found: Nonexistent Project")

    def test_delete_project_without_data_raises_error(self):
        """Test that deleting project without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.delete_project("Test")

    def test_delete_project_no_projects_section(self):
        """Test deleting when no projects section exists."""
        del self.cv.data['cv']['sections']['projects']
        result = self.cv.delete_project("Test")
        self.assertEqual(result, "No projects to delete")

    def test_modify_projects_info_success(self):
        """Test modifying project info successfully."""
        result = self.cv.modify_projects_info("Project Name", "summary", "New summary")
        self.assertEqual(result, "Successfully modified summary to New summary")

    def test_modify_projects_info_invalid_field(self):
        """Test modifying project with invalid field."""
        result = self.cv.modify_projects_info("Project Name", "invalid_field", "value")
        self.assertIn("Invalid field", result)

    def test_modify_projects_info_project_not_found(self):
        """Test modifying non-existent project."""
        result = self.cv.modify_projects_info("Nonexistent", "summary", "value")
        self.assertEqual(result, "Project Nonexistent not found.")

    def test_modify_projects_info_without_data_raises_error(self):
        """Test that modifying project without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.modify_projects_info("Test", "summary", "value")


class TestAddProjectFromAI(unittest.TestCase):
    """Tests for the add_project_from_ai method."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_add_project_from_ai_without_data_raises_error(self):
        """Test that adding project from AI without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError) as context:
            cv.add_project_from_ai("some_path.json")
        self.assertIn("No data loaded", str(context.exception))

    @patch('src.reporting.Generate_RenderCV_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_RenderCV_Resume.orjson.loads')
    def test_add_project_from_ai_success(self, mock_orjson, mock_open, mock_generate_resume):
        """Test successfully adding a project from AI analysis."""
        # Setup mocks
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

        self.assertEqual(result, "Successfully added: AI Generated Project")
        mock_generate_resume.assert_called_once_with('/fake/project/path')

    @patch('src.reporting.Generate_RenderCV_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_RenderCV_Resume.orjson.loads')
    def test_add_project_from_ai_includes_tech_stack_in_summary(self, mock_orjson, mock_open, mock_generate_resume):
        """Test that tech stack is appended to the summary."""
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "Tech Project"
        mock_ai_resume.one_sentence_summary = "A cool project"
        mock_ai_resume.tech_stack = "React, Node.js"
        mock_ai_resume.key_responsibilities = ["Feature 1"]
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        self.cv.add_project_from_ai("project.json")

        # Find the added project
        added_project = next(
            (p for p in self.cv.current_projects if p['name'] == "Tech Project"), None
        )
        self.assertIsNotNone(added_project)
        self.assertIn("Tech stack: React, Node.js", added_project['summary'])

    @patch('src.reporting.Generate_RenderCV_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_RenderCV_Resume.orjson.loads')
    def test_add_project_from_ai_without_tech_stack(self, mock_orjson, mock_open, mock_generate_resume):
        """Test adding project when tech_stack is empty."""
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "Simple Project"
        mock_ai_resume.one_sentence_summary = "A simple project"
        mock_ai_resume.tech_stack = ""  # Empty tech stack
        mock_ai_resume.key_responsibilities = ["Did something"]
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        self.cv.add_project_from_ai("project.json")

        added_project = next(
            (p for p in self.cv.current_projects if p['name'] == "Simple Project"), None
        )
        self.assertIsNotNone(added_project)
        self.assertEqual(added_project['summary'], "A simple project")
        self.assertNotIn("Tech stack", added_project['summary'])

    @patch('src.reporting.Generate_RenderCV_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_RenderCV_Resume.orjson.loads')
    def test_add_project_from_ai_duplicate_rejected(self, mock_orjson, mock_open, mock_generate_resume):
        """Test that duplicate AI-generated projects are rejected."""
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        # Use the name of an existing project from the starter template
        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "Project Name"  # Exists in starter template
        mock_ai_resume.one_sentence_summary = "Summary"
        mock_ai_resume.tech_stack = ""
        mock_ai_resume.key_responsibilities = []
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        result = self.cv.add_project_from_ai("project.json")

        self.assertIn("already exists", result)

    def test_add_project_from_ai_file_not_found(self):
        """Test that FileNotFoundError is raised when project file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            self.cv.add_project_from_ai("nonexistent_file.json")

    @patch('src.reporting.Generate_RenderCV_Resume.GenerateProjectResume')
    @patch('builtins.open', create=True)
    @patch('src.reporting.Generate_RenderCV_Resume.orjson.loads')
    def test_add_project_from_ai_sets_correct_highlights(self, mock_orjson, mock_open, mock_generate_resume):
        """Test that key_responsibilities are correctly set as highlights."""
        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_file = MagicMock()
        mock_file.read.return_value = b'{}'
        mock_open.return_value.__enter__.return_value = mock_file

        expected_highlights = ["Implemented feature A", "Optimized performance by 50%", "Led team of 3"]
        mock_ai_resume = MagicMock()
        mock_ai_resume.project_title = "Highlight Test Project"
        mock_ai_resume.one_sentence_summary = "Test summary"
        mock_ai_resume.tech_stack = ""
        mock_ai_resume.key_responsibilities = expected_highlights
        mock_generate_resume.return_value.generate.return_value = mock_ai_resume

        self.cv.add_project_from_ai("project.json")

        added_project = next(
            (p for p in self.cv.current_projects if p['name'] == "Highlight Test Project"), None
        )
        self.assertIsNotNone(added_project)
        self.assertEqual(added_project['highlights'], expected_highlights)


class TestCreateRenderCVSections(unittest.TestCase):
    """Tests for section-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_remove_section_success(self):
        """Test removing a section successfully."""
        initial_sections = len(self.cv.data['cv']['sections'])
        self.cv.remove_section(0)  # Remove first section after summary
        self.assertEqual(len(self.cv.data['cv']['sections']), initial_sections - 1)

    def test_remove_section_without_data_raises_error(self):
        """Test that removing section without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.remove_section(0)


class TestCreateRenderCVContact(unittest.TestCase):
    """Tests for contact-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_update_contact_email(self):
        """Test updating email."""
        self.cv.update_contact(email="new@email.com")
        self.assertEqual(self.cv.data['cv']['email'], "new@email.com")

    def test_update_contact_phone(self):
        """Test updating phone."""
        self.cv.update_contact(phone="+1 999 888 7777")
        self.assertEqual(self.cv.data['cv']['phone'], "+1 999 888 7777")

    def test_update_contact_location(self):
        """Test updating location."""
        self.cv.update_contact(location="New York, NY")
        self.assertEqual(self.cv.data['cv']['location'], "New York, NY")

    def test_update_contact_website(self):
        """Test updating website."""
        self.cv.update_contact(website="https://newsite.com")
        self.assertEqual(self.cv.data['cv']['website'], "https://newsite.com")

    def test_update_contact_name(self):
        """Test updating name."""
        self.cv.update_contact(name="New Name")
        self.assertEqual(self.cv.data['cv']['name'], "New Name")

    def test_update_contact_multiple_fields(self):
        """Test updating multiple contact fields at once."""
        self.cv.update_contact(
            email="test@test.com",
            phone="+1 111 222 3333",
            location="Boston, MA"
        )
        self.assertEqual(self.cv.data['cv']['email'], "test@test.com")
        self.assertEqual(self.cv.data['cv']['phone'], "+1 111 222 3333")
        self.assertEqual(self.cv.data['cv']['location'], "Boston, MA")

    def test_update_contact_without_data_raises_error(self):
        """Test that updating contact without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.update_contact(email="test@test.com")

    def test_update_contact_returns_self(self):
        """Test that update_contact returns self for method chaining."""
        result = self.cv.update_contact(email="test@test.com")
        self.assertIs(result, self.cv)


class TestCreateRenderCVConnections(unittest.TestCase):
    """Tests for connection-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_add_connection_without_data_raises_error(self):
        """Test that adding connection without loaded data raises ValueError."""
        cv = create_Render_CV()
        conn = Connections(network="Twitter", username="testuser")
        with self.assertRaises(ValueError):
            cv.add_connection(conn)

    def test_add_connection_success(self):
        """Test that add_connection adds a new connection successfully."""
        conn = Connections(network="Twitter", username="testuser")
        result = self.cv.add_connection(conn)
        self.assertEqual(result, "Successfully added: Twitter")

    def test_add_connection_duplicate_rejected(self):
        """Test that duplicate connections are rejected."""
        conn = Connections(network="LinkedIn", username="testuser")
        result = self.cv.add_connection(conn)
        self.assertEqual(result, "Connection already exists in Resume")


class TestCreateRenderCVAutoSave(unittest.TestCase):
    """Tests for auto-save functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_auto_save_enabled_saves_on_modification(self):
        """Test that auto_save triggers save on modification."""
        cv = create_Render_CV(auto_save=True)
        cv.generate_starter_file(name="Test User")
        cv.load_starter_file()

        with patch.object(cv, 'save') as mock_save:
            edu = Education(institution="Auto Save Test", areaOfStudy="Testing")
            cv.add_education(edu)
            mock_save.assert_called()

    def test_auto_save_disabled_no_save_on_modification(self):
        """Test that disabled auto_save doesn't trigger save."""
        cv = create_Render_CV(auto_save=False)
        cv.generate_starter_file(name="Test User")
        cv.load_starter_file()

        with patch.object(cv, 'save') as mock_save:
            edu = Education(institution="No Auto Save Test", areaOfStudy="Testing")
            cv.add_education(edu)
            mock_save.assert_not_called()


class TestCreateRenderCVRender(unittest.TestCase):
    """Tests for render functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_render_cv_file_not_found(self):
        """Test that render raises error when file doesn't exist."""
        cv = create_Render_CV()
        cv.yaml_file = Path("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            cv.render_CV()

    @patch('subprocess.run')
    def test_render_cv_calls_subprocess(self, mock_run):
        """Test that render_CV calls subprocess with correct arguments."""
        mock_run.return_value = MagicMock(returncode=1)
        self.cv.render_CV()
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn('rendercv', call_args[0][0])
        self.assertIn('render', call_args[0][0])


class TestThemes(unittest.TestCase):
    """Tests for theme functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_available_themes(self):
        """Test that themes dictionary contains expected themes."""
        cv = create_Render_CV()
        expected_themes = ['classic', 'engineeringclassic', 'engineeringresumes', 'moderncv', 'sb2nov']
        for theme in expected_themes:
            self.assertIn(theme, cv.themes)

    def test_default_theme_is_sb2nov(self):
        """Test that default theme is sb2nov."""
        cv = create_Render_CV()
        self.assertEqual(cv.chosen_theme, 'sb2nov')

    def test_update_theme_success(self):
        """Test updating theme successfully."""
        result = self.cv.update_theme('classic')
        self.assertEqual(result, "Successfully updated: classic")
        self.assertEqual(self.cv.data['design']['theme'], 'classic')


class TestCreateRenderCVSkills(unittest.TestCase):
    """Tests for skill-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_add_skills_success(self):
        """Test adding a skill successfully."""
        skill = Skills(label="Testing", details="Unit testing, Integration testing")
        result = self.cv.add_skills(skill)
        self.assertEqual(result, "Successfully added skills")

    def test_add_skills_without_data_raises_error(self):
        """Test that adding skill without loaded data raises ValueError."""
        cv = create_Render_CV()
        skill = Skills(label="Testing", details="Unit testing")
        with self.assertRaises(ValueError):
            cv.add_skills(skill)

    def test_add_skills_duplicate_rejected(self):
        """Test that duplicate skills are rejected."""
        skill = Skills(label="Languages", details="Python, Java")  # Already exists in starter
        result = self.cv.add_skills(skill)
        self.assertEqual(result, "Duplicate label/skills")

    def test_add_skills_creates_section_if_missing(self):
        """Test that skills section is created if it doesn't exist."""
        del self.cv.data['cv']['sections']['skills']
        self.cv.current_skills = []
        skill = Skills(label="New Skill", details="Details here")
        self.cv.add_skills(skill)
        self.assertIn('skills', self.cv.data['cv']['sections'])

    def test_modify_skill_success(self):
        """Test modifying a skill successfully."""
        result = self.cv.modify_skill("Languages", "Python, Java, Go, Rust")
        self.assertEqual(result, "Successfully modified skill")
        # Verify the skill was actually modified
        skill = next((s for s in self.cv.current_skills if s.get('label') == 'Languages'), None)
        self.assertEqual(skill['details'], "Python, Java, Go, Rust")

    def test_modify_skill_without_data_raises_error(self):
        """Test that modifying skill without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.modify_skill("Languages", "Python")

    def test_modify_skill_not_found(self):
        """Test modifying a non-existent skill."""
        result = self.cv.modify_skill("Nonexistent Skill", "Some details")
        self.assertEqual(result, "Skill not found.")

    def test_delete_skill_success(self):
        """Test deleting a skill successfully."""
        result = self.cv.delete_skill("Languages")
        self.assertEqual(result, "Successfully deleted chosen skill")
        # Verify the skill was actually deleted
        skill = next((s for s in self.cv.current_skills if s.get('label') == 'Languages'), None)
        self.assertIsNone(skill)

    def test_delete_skill_without_data_raises_error(self):
        """Test that deleting skill without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.delete_skill("Languages")

    def test_delete_skill_not_found(self):
        """Test deleting a non-existent skill."""
        result = self.cv.delete_skill("Nonexistent Skill")
        self.assertEqual(result, "skill not found")

    def test_delete_skill_no_skills_section(self):
        """Test deleting when no skills section exists."""
        del self.cv.data['cv']['sections']['skills']
        self.cv.current_skills = []
        result = self.cv.delete_skill("Languages")
        self.assertEqual(result, "No skills found to be deleted.")


class TestCreateRenderCVConnectionModifications(unittest.TestCase):
    """Tests for connection modification and deletion methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.cv = create_Render_CV(auto_save=False)
        self.cv.generate_starter_file(name="Test User")
        self.cv.load_starter_file()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up test files from project directory
        cv_dir = Path(__file__).parent.parent / "User_config_files" / "Generate_render_CV_files"
        for f in cv_dir.glob("Test_User_CV.yaml"):
            f.unlink(missing_ok=True)

    def test_modify_connection_success(self):
        """Test modifying a connection username successfully."""
        result = self.cv.modify_connection("LinkedIn", "new_linkedin_user")
        self.assertEqual(result, "Successfully updated connection LinkedIn")
        # Verify the connection was actually modified
        conn = next((c for c in self.cv.current_connections if c.get('network') == 'LinkedIn'), None)
        self.assertEqual(conn['username'], "new_linkedin_user")

    def test_modify_connection_without_data_raises_error(self):
        """Test that modifying connection without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.modify_connection("LinkedIn", "newuser")

    def test_modify_connection_not_found(self):
        """Test modifying a non-existent connection."""
        result = self.cv.modify_connection("Twitter", "testuser")
        self.assertEqual(result, "Network Twitter Cannot be found.")

    def test_delete_connection_success(self):
        """Test deleting a connection successfully."""
        result = self.cv.delete_connection("LinkedIn")
        self.assertEqual(result, "Successfully deleted connection: LinkedIn")
        # Verify the connection was actually deleted
        conn = next((c for c in self.cv.current_connections if c.get('network') == 'LinkedIn'), None)
        self.assertIsNone(conn)

    def test_delete_connection_without_data_raises_error(self):
        """Test that deleting connection without loaded data raises ValueError."""
        cv = create_Render_CV()
        with self.assertRaises(ValueError):
            cv.delete_connection("LinkedIn")

    def test_delete_connection_not_found(self):
        """Test deleting a non-existent connection."""
        result = self.cv.delete_connection("Twitter")
        self.assertEqual(result, "Connection 'Twitter' not found")

    def test_delete_connection_no_connections(self):
        """Test deleting when no social_networks section exists."""
        del self.cv.data['cv']['social_networks']
        result = self.cv.delete_connection("LinkedIn")
        self.assertEqual(result, "No connections to delete")

    def test_delete_connection_empty_list(self):
        """Test deleting when social_networks is empty list."""
        self.cv.data['cv']['social_networks'] = []
        self.cv.current_connections = []
        result = self.cv.delete_connection("LinkedIn")
        self.assertEqual(result, "No connections to delete")


if __name__ == '__main__':
    unittest.main()
