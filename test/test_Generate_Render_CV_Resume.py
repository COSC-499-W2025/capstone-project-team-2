import unittest
import os
import gc
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")

from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    Education, Connections, Project, Skills, Experience, RenderCVDocument,
)


class BaseRenderCVTest(unittest.TestCase):
    """Base class with common setup/teardown for all RenderCV tests."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        gc.collect()

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gc.collect()

    def create_loaded_cv(self, doc_type='resume', auto_save=False):
        """Create a CV instance with starter file generated and loaded."""
        cv = RenderCVDocument(doc_type=doc_type, auto_save=auto_save)
        cv.cv_files_dir = Path(self.test_dir)
        cv.generate(name="Test User")
        cv.load()
        return cv


class TestRenderCVDocumentCore(BaseRenderCVTest):
    """Tests for initialization, generation, loading, and saving."""

    def test_init_and_defaults(self):
        """Test initialization with default and custom values."""
        cv = RenderCVDocument()
        self.assertTrue(cv.auto_save)
        self.assertEqual(cv.chosen_theme, 'sb2nov')
        self.assertEqual(cv.doc_type, 'resume')
        self.assertIsNone(cv.data)

        cv2 = RenderCVDocument(doc_type='portfolio', auto_save=False, output_dir='custom')
        self.assertFalse(cv2.auto_save)
        self.assertEqual(cv2.doc_type, 'portfolio')

    def test_generate(self):
        """Test file generation operations."""
        cv = RenderCVDocument(doc_type='resume')
        cv.cv_files_dir = Path(self.test_dir)

        # Generate new file
        result = cv.generate(name="John Doe")
        self.assertEqual(result, "Success")
        self.assertEqual(cv.name, "John_Doe")
        self.assertTrue(cv.yaml_file.exists())

        # Skip existing file when overwrite=False
        self.assertEqual(cv.generate(name="John Doe", overwrite=False), "Skipping generation")

    def test_load(self):
        """Test file loading operations."""
        # Setup: generate a file first
        cv = RenderCVDocument(doc_type='resume')
        cv.cv_files_dir = Path(self.test_dir)
        cv.generate(name="John Doe")

        # Load the generated file
        data = cv.load()
        self.assertIn('cv', data)
        self.assertIsNotNone(cv.sections)
        self.assertIsInstance(cv.summary, list)

        # Load by name
        cv2 = RenderCVDocument(doc_type='resume')
        cv2.cv_files_dir = Path(self.test_dir)
        cv2.load(name="John Doe")
        self.assertEqual(cv2.name, "John_Doe")

        # Load non-existent file raises error
        cv3 = RenderCVDocument()
        cv3.yaml_file = Path("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            cv3.load()

    def test_save(self):
        """Test file saving operations."""
        # Setup: generate and load a file first
        cv = RenderCVDocument(doc_type='resume')
        cv.cv_files_dir = Path(self.test_dir)
        cv.generate(name="John Doe")
        cv.load()

        # Save the file
        output = cv.save()
        self.assertTrue(output.exists())

        # Save without data raises error
        cv2 = RenderCVDocument()
        with self.assertRaises(ValueError):
            cv2.save()

    def test_render(self):
        """Test render functionality."""
        cv = self.create_loaded_cv()

        # File not found
        cv2 = RenderCVDocument()
        cv2.yaml_file = Path("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            cv2.render()

        # Subprocess called
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            cv.render()
            mock_run.assert_called_once()

    def test_render_outputs_pdf_html_markdown(self):
        """Test multi-format rendering and renaming."""
        cv = self.create_loaded_cv()
        output_dir = cv.yaml_file.parent / "rendercv_output"
        output_base = f"{cv.name}_CV"

        def fake_run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"):
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{output_base}.pdf").write_text("pdf")
            (output_dir / f"{output_base}.html").write_text("html")
            (output_dir / f"{output_base}.md").write_text("md")
            return MagicMock(returncode=0, stderr="", stdout="")

        with patch('subprocess.run', side_effect=fake_run) as mock_run:
            status, outputs = cv.render_outputs(["pdf", "html", "markdown"])

        self.assertEqual(status, "successfully rendered")
        self.assertIn("pdf", outputs)
        self.assertIn("html", outputs)
        self.assertIn("markdown", outputs)
        self.assertTrue((output_dir / f"{cv.name}_Resume.pdf").exists())
        self.assertTrue((output_dir / f"{cv.name}_Resume.html").exists())
        self.assertTrue((output_dir / f"{cv.name}_Resume.md").exists())

        called_cmd = mock_run.call_args[0][0]
        self.assertNotIn("--dont-generate-pdf", called_cmd)
        self.assertNotIn("--dont-generate-html", called_cmd)
        self.assertNotIn("--dont-generate-markdown", called_cmd)
        self.assertNotIn("--dont-generate-typst", called_cmd)

    def test_render_outputs_html_only(self):
        """Test HTML-only rendering keeps HTML and removes markdown."""
        cv = self.create_loaded_cv()
        output_dir = cv.yaml_file.parent / "rendercv_output"
        output_base = f"{cv.name}_CV"

        def fake_run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"):
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{output_base}.html").write_text("html")
            (output_dir / f"{output_base}.md").write_text("md")
            return MagicMock(returncode=0, stderr="", stdout="")

        with patch('subprocess.run', side_effect=fake_run) as mock_run:
            status, outputs = cv.render_outputs(["html"])

        self.assertEqual(status, "successfully rendered")
        self.assertIn("html", outputs)
        self.assertNotIn("markdown", outputs)
        self.assertFalse((output_dir / f"{output_base}.md").exists())

        called_cmd = mock_run.call_args[0][0]
        self.assertIn("--dont-generate-pdf", called_cmd)
        self.assertIn("--dont-generate-typst", called_cmd)
        self.assertNotIn("--dont-generate-html", called_cmd)
        self.assertNotIn("--dont-generate-markdown", called_cmd)

    def test_render_outputs_invalid_format(self):
        """Test unsupported format raises error."""
        cv = self.create_loaded_cv()
        with self.assertRaises(ValueError):
            cv.render_outputs(["docx"])

class TestRequiresDataDecorator(BaseRenderCVTest):
    """Test that all data-requiring operations raise ValueError when data not loaded."""

    def test_operations_without_data_raise_error(self):
        cv = RenderCVDocument(doc_type='resume')
        operations = [
            (cv.add_education, (Education(institution="Test", area="Test"),)),
            (cv.remove_education, ("Test",)),
            (cv.add_experience, (Experience(company="Test"),)),
            (cv.remove_experience, ("Test",)),
            (cv.add_project, (Project(name="Test"),)),
            (cv.remove_project, ("Test",)),
            (cv.add_skills, (Skills(label="Test", details="Test"),)),
            (cv.remove_skill, ("Test",)),
            (cv.add_connection, (Connections(network="Test", username="test"),)),
            (cv.remove_connection, ("Test",)),
            (cv.update_contact, (), {"email": "test@test.com"}),
        ]
        for op in operations:
            func, args = op[0], op[1]
            kwargs = op[2] if len(op) == 3 else {}
            with self.assertRaises(ValueError):
                func(*args, **kwargs)


class TestEducationAndExperience(BaseRenderCVTest):
    """Tests for education and experience operations."""

    def test_education_crud(self):
        """Test add and remove education."""
        cv = self.create_loaded_cv()

        # Add success
        self.assertEqual(cv.add_education(Education(institution="New Uni", area="CS")), "Successfully added education")
        # Duplicate
        self.assertEqual(cv.add_education(Education(institution="University Name", area="CS")), "Duplicate education entry")
        # Not found
        self.assertIn("not found", cv.remove_education("Nonexistent"))
        # Success remove
        self.assertEqual(cv.remove_education("University Name"), "Successfully deleted education")
        self.assertEqual(cv.remove_education("New Uni"), "Successfully deleted education")
        # No education left
        self.assertEqual(cv.remove_education("Test"), "No education to delete")

    def test_experience_crud(self):
        """Test add and remove experience."""
        cv = self.create_loaded_cv()

        # Add success
        self.assertEqual(cv.add_experience(Experience(company="New Co", position="Dev")), "Successfully added experience")
        # Empty company rejected
        self.assertEqual(cv.add_experience(Experience(company="", position="Dev")), "Company name cannot be empty")
        # Not found
        self.assertIn("not found", cv.remove_experience("Nonexistent"))
        # Success remove
        self.assertEqual(cv.remove_experience("Company Name"), "Successfully removed experience")
        self.assertEqual(cv.remove_experience("New Co"), "Successfully removed experience")
        # No experience left
        self.assertEqual(cv.remove_experience("Test"), "No experience to delete")


class TestProjectsAndSkills(BaseRenderCVTest):
    """Tests for projects and skills operations."""

    def test_projects_crud(self):
        """Test add, modify, and remove projects."""
        cv = self.create_loaded_cv()

        # Add success
        self.assertIn("Successfully added", cv.add_project(Project(name="New Project")))
        # Duplicate
        self.assertIn("already exists", cv.add_project(Project(name="Project Name")))
        # Modify success
        self.assertIn("Successfully modified", cv.modify_project("Project Name", "summary", "New summary"))
        # Modify invalid field
        self.assertIn("Invalid field", cv.modify_project("Project Name", "invalid", "value"))
        # Modify not found
        self.assertIn("not found", cv.modify_project("Nonexistent", "summary", "value"))
        # Remove not found
        self.assertIn("not found", cv.remove_project("Nonexistent"))
        # Remove success
        self.assertIn("Successfully deleted", cv.remove_project("Project Name"))

    def test_skills_crud(self):
        """Test add and remove skills."""
        cv = self.create_loaded_cv()

        # Add success
        self.assertEqual(cv.add_skills(Skills(label="Testing", details="Unit tests")), "Successfully added skills")
        # Duplicate
        self.assertEqual(cv.add_skills(Skills(label="Languages", details="Python")), "Duplicate skill label")
        # Empty label rejected
        self.assertEqual(cv.add_skills(Skills(label="", details="Test")), "Skill label cannot be empty")
        # Remove success
        self.assertEqual(cv.remove_skill("Languages"), "Successfully deleted skill")
        # Not found
        self.assertIn("not found", cv.remove_skill("Nonexistent"))

    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.GenerateProjectResume')
    @patch('src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume.orjson.loads')
    def test_add_project_from_ai(self, mock_orjson, mock_generate_resume):
        """Test AI-powered project generation."""
        cv = self.create_loaded_cv()

        mock_orjson.return_value = {'project_root': '/fake/path'}
        mock_ai = MagicMock()
        mock_ai.project_title = "AI Project"
        mock_ai.one_sentence_summary = "AI summary"
        mock_ai.tech_stack = "Python"
        mock_ai.key_responsibilities = ["Task 1"]
        mock_generate_resume.return_value.generate.return_value = mock_ai

        with patch('builtins.open', mock_open(read_data=b'{}')):
            result = cv.add_project_from_ai("project.json")
            self.assertIn("AI Project", result)

        # Duplicate rejected
        with patch('builtins.open', mock_open(read_data=b'{}')):
            mock_ai.project_title = "Project Name"
            result = cv.add_project_from_ai("project.json")
            self.assertIn("already exists", result)

        # Without data raises error
        cv2 = RenderCVDocument()
        with self.assertRaises(ValueError):
            cv2.add_project_from_ai("path.json")


class TestConnectionsAndContact(BaseRenderCVTest):
    """Tests for connections and contact operations."""

    def test_connections_crud(self):
        """Test add, modify, and remove connections."""
        cv = self.create_loaded_cv()

        # Add success
        self.assertEqual(cv.add_connection(Connections(network="Twitter", username="user")), "Successfully added: Twitter")
        # Duplicate
        self.assertIn("already exists", cv.add_connection(Connections(network="LinkedIn", username="user")))
        # Modify success
        self.assertIn("Successfully updated", cv.modify_connection("LinkedIn", "newuser"))
        # Modify not found
        self.assertIn("not found", cv.modify_connection("Facebook", "user"))
        # Remove success
        self.assertIn("Successfully deleted", cv.remove_connection("LinkedIn"))
        # Remove not found
        self.assertIn("not found", cv.remove_connection("Instagram"))
        # No connections
        cv.current_connections = []
        self.assertEqual(cv.remove_connection("Test"), "No connections to delete")

    def test_contact_and_theme(self):
        """Test contact updates and theme changes."""
        cv = self.create_loaded_cv()

        # Update contact (returns self for chaining)
        result = cv.update_contact(email="test@test.com", phone="123", location="NYC", name="New Name")
        self.assertIs(result, cv)
        self.assertEqual(cv.data['cv']['email'], "test@test.com")
        self.assertEqual(cv.data['cv']['name'], "New Name")

        # Theme update
        self.assertIn("Successfully updated", cv.update_theme('classic'))
        self.assertEqual(cv.data['design']['theme'], 'classic')

        # Invalid theme
        with self.assertRaises(ValueError):
            cv.update_theme('invalid_theme')

    def test_summary_crud(self):
        """Test update and get summary."""
        cv = self.create_loaded_cv()

        # Get default summary
        default_summary = cv.get_summary()
        self.assertIsInstance(default_summary, str)

        # Update summary
        result = cv.update_summary("This is my new professional summary.")
        self.assertEqual(result, "Summary updated successfully")
        self.assertEqual(cv.get_summary(), "This is my new professional summary.")

        # Update summary again
        cv.update_summary("Updated summary text.")
        self.assertEqual(cv.get_summary(), "Updated summary text.")

        # Portfolio also supports summary
        portfolio = self.create_loaded_cv(doc_type='portfolio')
        portfolio.update_summary("Portfolio summary")
        self.assertEqual(portfolio.get_summary(), "Portfolio summary")


class TestAutoSaveAndDocType(BaseRenderCVTest):
    """Tests for auto-save and document type restrictions."""

    def test_auto_save_behavior(self):
        """Test auto_save triggers or skips save."""
        # Auto-save enabled
        cv = self.create_loaded_cv(auto_save=True)
        with patch.object(cv, 'save') as mock_save:
            cv.add_education(Education(institution="Test", area="Test"))
            mock_save.assert_called()

        # Auto-save disabled
        cv2 = self.create_loaded_cv(auto_save=False)
        with patch.object(cv2, 'save') as mock_save:
            cv2.add_education(Education(institution="Test2", area="Test"))
            mock_save.assert_not_called()

    def test_portfolio_restrictions(self):
        """Test that resume-only methods raise ValueError for portfolio."""
        portfolio = self.create_loaded_cv(doc_type='portfolio')

        with self.assertRaises(ValueError):
            portfolio.add_education(Education(institution="Test", area="Test"))
        with self.assertRaises(ValueError):
            portfolio.add_experience(Experience(company="Test"))


if __name__ == '__main__':
    unittest.main()
