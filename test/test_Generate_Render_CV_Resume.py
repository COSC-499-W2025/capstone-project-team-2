import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add src directory to path
from src.reporting.Generate_RenderCV_Resume import (
    Education,
    Connections,
    Project,
    create_Render_CV
)


class TestCreateRenderCV(unittest.TestCase):
    """Tests for the create_Render_CV class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

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
        self.assertEqual(cv.yaml_file, Path("John_Doe_CV.yaml"))

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


if __name__ == '__main__':
    unittest.main()
