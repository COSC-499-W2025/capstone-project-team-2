import unittest
from src.resume_pdf_generator import SimpleResumeGenerator
from src.Generate_AI_Resume import GenerateProjectResume
from pathlib import Path
import tempfile
import os
import shutil


class TestPDFGenerator(unittest.TestCase):
    """
    Test case class for verifying the functionality of PDF generation routines.

    This class contains test methods to ensure the correctness of PDF generation,
    including the generation of multiple PDFs, verifying content, and handling
    custom filenames. It uses temporary directories for test isolation and cleanup.

    :ivar tempFolder: Path to a temporary folder for storing generated PDFs during testing.
    :type tempFolder: str
    :ivar test_folder: Path to the folder containing test scripts or related data.
    :type test_folder: Path
    :ivar instance: Instance of a pre-generated project resume loaded for testing purposes.
    :type instance: GenerateProjectResume
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class-level resources required for testing.

        This method creates a temporary directory to store generated PDFs and initializes
        the test resources from the specified folder. It also instantiates the necessary
        objects for generating project resumes based on the test scripts.

        :rtype: None
        """
        cls.tempFolder = tempfile.mkdtemp()  # Creates actual directory for PDFs
        root_folder = Path(__file__).resolve().parent
        cls.test_folder = root_folder / "tiny_scripts"
        cls.instance = GenerateProjectResume(cls.test_folder).generate(saveToJson=False)


    def test_save_pdf(self):
        """Test that PDF is created with a specified filename"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()  # Creates "Portfolio.pdf"

        expected_file = os.path.join(self.tempFolder, "Portfolio.pdf")
        self.assertTrue(os.path.exists(expected_file), f"PDF not found at {expected_file}")

    def test_one_line_resume(self):
        """Test that the one line resume is successfully generated"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()
        generator.create_resume_line()
        # Use the actual project title from the data
        expected_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_one_line_resume_not_empty(self):
        """
        Verifies that the generated one-line resume PDF is not empty and has a minimum size.
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()
        generator.create_resume_line()
        # Use the actual project title from the data
        expected_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")
        file_size = os.path.getsize(expected_file)
        self.assertGreater(file_size, 0, "PDF file is empty")
        self.assertGreater(file_size, 1000, "PDF file seems too small")




    def test_pdf_has_content(self):
        """Test that generated PDF has content (not empty)"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()

        expected_file = os.path.join(self.tempFolder, "Portfolio.pdf")
        file_size = os.path.getsize(expected_file)
        self.assertGreater(file_size, 0, "PDF file is empty")
        self.assertGreater(file_size, 1000, "PDF file seems too small")

    def test_multiple_pdf_generation(self):
        """Test generating multiple PDFs with different filenames"""
        pdf_filenames = ["Portfolio_1", "Portfolio_2", "Portfolio_3"]

        for filename in pdf_filenames:
            generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName=filename)
            generator.generate()  # Creates {fileName}.pdf

            expected_file = os.path.join(self.tempFolder, f"{filename}.pdf")
            self.assertTrue(os.path.exists(expected_file), f"PDF not found: {expected_file}")

    def test_custom_portfolio_filename(self):
        """Test generating PDF with custom filename"""
        custom_filename = "John_Doe_Portfolio"
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName=custom_filename)
        generator.generate()

        expected_file = os.path.join(self.tempFolder, f"{custom_filename}.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_pdf_saved_in_correct_folder(self):
        """Test that PDF is saved in the specified folder"""
        # Create a subfolder for this test
        sub_folder = os.path.join(self.tempFolder, "test_subfolder")
        os.makedirs(sub_folder, exist_ok=True)

        generator = SimpleResumeGenerator(sub_folder, data=self.instance, fileName="Test_Resume")
        generator.generate()

        expected_file = os.path.join(sub_folder, "Test_Resume.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_with_spaces_in_filename(self):
        """Test generating PDF with spaces in filename"""
        filename_with_spaces = "My Professional Portfolio"
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName=filename_with_spaces)
        generator.generate()

        expected_file = os.path.join(self.tempFolder, f"{filename_with_spaces}.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_display_portfolio(self):
        """Test that display_portfolio generates PDF and prints confirmation"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="DisplayPortfolioTest")
        generator.display_portfolio()

        expected_file = os.path.join(self.tempFolder, "DisplayPortfolioTest.pdf")
        self.assertTrue(os.path.exists(expected_file), f"PDF not found at {expected_file}")

    def test_display_resume_line(self):
        """Test that display_resume_line generates resume line PDF"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="DisplayResumeLineTest")
        generator.display_resume_line()

        expected_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")
        self.assertTrue(os.path.exists(expected_file), f"Resume line PDF not found at {expected_file}")

    def test_display_and_run(self):
        """Test that display_and_run generates both portfolio and resume line PDFs"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="DisplayAndRunTest")
        generator.display_and_run()

        portfolio_file = os.path.join(self.tempFolder, "DisplayAndRunTest.pdf")
        resume_line_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")

        self.assertTrue(os.path.exists(portfolio_file), f"Portfolio PDF not found at {portfolio_file}")
        self.assertTrue(os.path.exists(resume_line_file), f"Resume line PDF not found at {resume_line_file}")

    def test_overwrite_existing_pdf(self):
        """Test that generating a PDF overwrites existing file with same name"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="OverwriteTest")
        generator.generate()

        expected_file = os.path.join(self.tempFolder, "OverwriteTest.pdf")
        first_size = os.path.getsize(expected_file)

        # Generate again - should overwrite
        generator2 = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="OverwriteTest")
        generator2.generate()

        self.assertTrue(os.path.exists(expected_file))
        # File should still exist and have content
        second_size = os.path.getsize(expected_file)
        self.assertGreater(second_size, 0)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary files after all tests"""

        if os.path.exists(cls.tempFolder):
            try:
                shutil.rmtree(cls.tempFolder)
            except Exception as e:
                print(f"Warning: Could not clean up temp folder: {e}")















