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
        cls.tempFolder = tempfile.mkdtemp()  # Creates actual directory, not just path
        cls.save_location = os.path.join(cls.tempFolder, "Portfolio.pdf")
        root_folder = Path(__file__).resolve().parent
        cls.test_folder = root_folder / "tiny_scripts"
        cls.instance = GenerateProjectResume(cls.test_folder).generate(saveToJson=False)


    def test_save_pdf(self):
        generator = SimpleResumeGenerator(self.save_location, data=self.instance)
        generator.generate()  # Must call generate() to create the PDF!
        self.assertTrue(os.path.exists(self.save_location))

    def test_pdf_has_content(self):
        # Each test should be independent - create PDF in this test
        generator = SimpleResumeGenerator(self.save_location, data=self.instance)
        generator.generate()

        file_size = os.path.getsize(self.save_location)
        self.assertGreater(file_size, 0, "PDF file is empty")
        self.assertGreater(file_size, 1000, "PDF file seems too small")

    def test_multiple_pdf_generation(self):
        """Test generating multiple PDFs sequentially"""
        paths = [
            os.path.join(self.tempFolder, f"resume_{i}.pdf")
            for i in range(3)
        ]

        for path in paths:
            generator = SimpleResumeGenerator(path, data=self.instance)
            generator.generate()  # Must call generate()!
            self.assertTrue(os.path.exists(path))

    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files after all tests"""

        if os.path.exists(cls.tempFolder):
            try:
                shutil.rmtree(cls.tempFolder)
            except Exception as e:
                print(f"Warning: Could not clean up temp folder: {e}")















