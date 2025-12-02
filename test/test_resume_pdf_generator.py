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
        """Test that PDF is created with specified filename"""
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()  # Creates "Portfolio.pdf"

        expected_file = os.path.join(self.tempFolder, "Portfolio.pdf")
        self.assertTrue(os.path.exists(expected_file), f"PDF not found at {expected_file}")

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



    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files after all tests"""

        if os.path.exists(cls.tempFolder):
            try:
                shutil.rmtree(cls.tempFolder)
            except Exception as e:
                print(f"Warning: Could not clean up temp folder: {e}")















