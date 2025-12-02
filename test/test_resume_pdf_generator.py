import unittest
from src.resume_pdf_generator import SimpleResumeGenerator
from src.Generate_AI_Resume import GenerateProjectResume
from pathlib import Path
import tempfile
import os
import shutil


class TestPDFGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tempFolder = tempfile.mkdtemp()  # Creates actual directory for PDFs
        root_folder = Path(__file__).resolve().parent
        cls.test_folder = root_folder / "tiny_scripts"
        cls.instance = GenerateProjectResume(cls.test_folder).generate(saveToJson=False)


    def test_save_pdf(self):
        """Test that PDF is created with default name"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance)
        generator.generate()  # Creates "My Portfolio.pdf" by default

        expected_file = os.path.join(self.tempFolder, "My Portfolio.pdf")
        self.assertTrue(os.path.exists(expected_file), f"PDF not found at {expected_file}")

    def test_pdf_has_content(self):
        """Test that generated PDF has content (not empty)"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance)
        generator.generate()

        expected_file = os.path.join(self.tempFolder, "My Portfolio.pdf")
        file_size = os.path.getsize(expected_file)
        self.assertGreater(file_size, 0, "PDF file is empty")
        self.assertGreater(file_size, 1000, "PDF file seems too small")

    def test_multiple_pdf_generation(self):
        """Test generating multiple PDFs with different names"""
        pdf_names = ["Portfolio_1", "Portfolio_2", "Portfolio_3"]

        for name in pdf_names:
            generator = SimpleResumeGenerator(self.tempFolder, data=self.instance)
            generator.generate(name=name)  # Creates {name}.pdf

            expected_file = os.path.join(self.tempFolder, f"{name}.pdf")
            self.assertTrue(os.path.exists(expected_file), f"PDF not found: {expected_file}")

    def test_custom_portfolio_name(self):
        """Test generating PDF with custom name"""
        custom_name = "John_Doe_Portfolio"
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance)
        generator.generate(name=custom_name)

        expected_file = os.path.join(self.tempFolder, f"{custom_name}.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_pdf_saved_in_correct_folder(self):
        """Test that PDF is saved in the specified folder"""
        # Create a subfolder for this test
        sub_folder = os.path.join(self.tempFolder, "test_subfolder")
        os.makedirs(sub_folder, exist_ok=True)

        generator = SimpleResumeGenerator(sub_folder, data=self.instance)
        generator.generate(name="Test_Resume")

        expected_file = os.path.join(sub_folder, "Test_Resume.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_with_spaces_in_name(self):
        """Test generating PDF with spaces in filename"""
        name_with_spaces = "My Professional Portfolio"
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance)
        generator.generate(name=name_with_spaces)

        expected_file = os.path.join(self.tempFolder, f"{name_with_spaces}.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_minimal_resume_data(self):
        """Test PDF generation with minimal resume data"""
        from src.Generate_AI_Resume import ResumeItem

        minimal_data = ResumeItem(
            project_title="Minimal Project",
            one_sentence_summary="",
            detailed_summary="A simple project with minimal data.",
            key_responsibilities=[],
            key_skills_used=[],
            tech_stack="",
            impact="",
            oop_principles_detected={}
        )

        generator = SimpleResumeGenerator(self.tempFolder, data=minimal_data)
        generator.generate(name="Minimal_Portfolio")

        expected_file = os.path.join(self.tempFolder, "Minimal_Portfolio.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_complete_resume_data(self):
        """Test PDF generation with complete resume data"""
        from src.Generate_AI_Resume import ResumeItem, OOPPrinciple

        complete_data = ResumeItem(
            project_title="Complete Test Project",
            one_sentence_summary="A fully featured test project",
            detailed_summary="This project demonstrates all resume fields populated.",
            key_responsibilities=[
                "Design system architecture",
                "Write comprehensive tests",
                "Deploy to production"
            ],
            key_skills_used=["Python", "Testing", "CI/CD", "Docker"],
            tech_stack="Python, pytest, Docker, AWS",
            impact="Increased test coverage by 80% and reduced deployment time by 50%",
            oop_principles_detected={
                "encapsulation": OOPPrinciple(
                    present=True,
                    description="Used private methods",
                    code_snippets=[]
                )
            }
        )

        generator = SimpleResumeGenerator(self.tempFolder, data=complete_data)
        generator.generate(name="Complete_Portfolio")

        expected_file = os.path.join(self.tempFolder, "Complete_Portfolio.pdf")
        self.assertTrue(os.path.exists(expected_file))

        # Should be larger than minimal
        file_size = os.path.getsize(expected_file)
        self.assertGreater(file_size, 2000, "Complete portfolio should be larger")

    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files after all tests"""

        if os.path.exists(cls.tempFolder):
            try:
                shutil.rmtree(cls.tempFolder)
            except Exception as e:
                print(f"Warning: Could not clean up temp folder: {e}")















