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
        """
        Test that a PDF file is created with a specified filename.

        This test verifies that the SimpleResumeGenerator correctly creates a PDF
        file at the expected location when the generate() method is called with
        a specific filename.

        :raises AssertionError: If the PDF file is not found at the expected path.
        :rtype: None
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()  # Creates "Portfolio.pdf"

        expected_file = os.path.join(self.tempFolder, "Portfolio.pdf")
        self.assertTrue(os.path.exists(expected_file), f"PDF not found at {expected_file}")

    def test_one_line_resume(self):
        """
        Test that the one-line resume PDF is successfully generated.

        This test verifies that the create_resume_line() method creates a separate
        PDF file containing a condensed one-line summary of the resume. The file
        is named using the project title with '_resume_line.pdf' suffix.

        :raises AssertionError: If the resume line PDF file is not found.
        :rtype: None
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()
        generator.create_resume_line()
        # Use the actual project title from the data
        expected_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_one_line_resume_not_empty(self):
        """
        Verify that the generated one-line resume PDF is not empty and has valid content.

        This test ensures that the resume line PDF contains actual content by checking
        that the file size is greater than zero and exceeds a minimum threshold of 1000
        bytes, which indicates the PDF has meaningful content rather than being corrupt
        or empty.

        :raises AssertionError: If the PDF file is empty or smaller than 1000 bytes.
        :rtype: None
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
        """
        Test that the generated portfolio PDF has valid content.

        This test verifies that the generated PDF file contains actual content
        by checking the file size. The file must be non-empty and exceed a
        minimum threshold of 1000 bytes to ensure it contains meaningful
        portfolio information.

        :raises AssertionError: If the PDF file is empty or smaller than 1000 bytes.
        :rtype: None
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="Portfolio")
        generator.generate()

        expected_file = os.path.join(self.tempFolder, "Portfolio.pdf")
        file_size = os.path.getsize(expected_file)
        self.assertGreater(file_size, 0, "PDF file is empty")
        self.assertGreater(file_size, 1000, "PDF file seems too small")

    def test_multiple_pdf_generation(self):
        """
        Test generating multiple PDF files with different filenames.

        This test verifies that the SimpleResumeGenerator can create multiple
        PDF files in succession, each with a unique filename. It ensures that
        the generator does not interfere with previously created files and
        correctly handles batch PDF generation.

        :raises AssertionError: If any of the expected PDF files are not found.
        :rtype: None
        """
        pdf_filenames = ["Portfolio_1", "Portfolio_2", "Portfolio_3"]

        for filename in pdf_filenames:
            generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName=filename)
            generator.generate()  # Creates {fileName}.pdf

            expected_file = os.path.join(self.tempFolder, f"{filename}.pdf")
            self.assertTrue(os.path.exists(expected_file), f"PDF not found: {expected_file}")

    def test_custom_portfolio_filename(self):
        """
        Test generating a PDF with a custom user-defined filename.

        This test verifies that the SimpleResumeGenerator correctly uses a custom
        filename provided by the user when creating the portfolio PDF. This is
        important for allowing users to personalize their portfolio filenames.

        :raises AssertionError: If the PDF with the custom filename is not found.
        :rtype: None
        """
        custom_filename = "John_Doe_Portfolio"
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName=custom_filename)
        generator.generate()

        expected_file = os.path.join(self.tempFolder, f"{custom_filename}.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_pdf_saved_in_correct_folder(self):
        """
        Test that the PDF is saved in the specified output folder.

        This test verifies that the SimpleResumeGenerator respects the folder path
        parameter and saves the generated PDF in the correct location. It creates
        a subfolder within the temporary directory to ensure the generator properly
        handles nested directory paths.

        :raises AssertionError: If the PDF is not found in the specified subfolder.
        :rtype: None
        """
        # Create a subfolder for this test
        sub_folder = os.path.join(self.tempFolder, "test_subfolder")
        os.makedirs(sub_folder, exist_ok=True)

        generator = SimpleResumeGenerator(sub_folder, data=self.instance, fileName="Test_Resume")
        generator.generate()

        expected_file = os.path.join(sub_folder, "Test_Resume.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_with_spaces_in_filename(self):
        """
        Test generating a PDF with spaces in the filename.

        This test verifies that the SimpleResumeGenerator correctly handles filenames
        containing spaces. This is important for usability as users may want to create
        portfolio files with natural language names like "My Professional Portfolio".

        :raises AssertionError: If the PDF with spaces in the filename is not found.
        :rtype: None
        """
        filename_with_spaces = "My Professional Portfolio"
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName=filename_with_spaces)
        generator.generate()

        expected_file = os.path.join(self.tempFolder, f"{filename_with_spaces}.pdf")
        self.assertTrue(os.path.exists(expected_file))

    def test_display_portfolio(self):
        """
        Test that display_portfolio generates the PDF and outputs a confirmation message.

        This test verifies that the display_portfolio() method correctly calls the
        generate() method internally and produces the expected PDF file. The method
        also prints a confirmation message to stdout indicating where the file was saved.

        :raises AssertionError: If the PDF file is not found at the expected path.
        :rtype: None
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="DisplayPortfolioTest")
        generator.display_portfolio()

        expected_file = os.path.join(self.tempFolder, "DisplayPortfolioTest.pdf")
        self.assertTrue(os.path.exists(expected_file), f"PDF not found at {expected_file}")

    def test_display_resume_line(self):
        """
        Test that display_resume_line generates the resume line PDF.

        This test verifies that the display_resume_line() method correctly calls
        create_resume_line() internally and produces the expected one-line resume
        PDF file. The file is named using the project title with '_resume_line.pdf'
        suffix and a confirmation message is printed to stdout.

        :raises AssertionError: If the resume line PDF is not found at the expected path.
        :rtype: None
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="DisplayResumeLineTest")
        generator.display_resume_line()

        expected_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")
        self.assertTrue(os.path.exists(expected_file), f"Resume line PDF not found at {expected_file}")

    def test_display_and_run(self):
        """
        Test that display_and_run generates both portfolio and resume line PDFs.

        This test verifies that the display_and_run() method correctly orchestrates
        the generation of both the full portfolio PDF and the one-line resume PDF
        in a single method call. This is the primary convenience method for users
        who want to generate all resume artifacts at once.

        :raises AssertionError: If either the portfolio or resume line PDF is not found.
        :rtype: None
        """
        generator = SimpleResumeGenerator(self.tempFolder, data=self.instance, fileName="DisplayAndRunTest")
        generator.display_and_run()

        portfolio_file = os.path.join(self.tempFolder, "DisplayAndRunTest.pdf")
        resume_line_file = os.path.join(self.tempFolder, f"{self.instance.project_title}_resume_line.pdf")

        self.assertTrue(os.path.exists(portfolio_file), f"Portfolio PDF not found at {portfolio_file}")
        self.assertTrue(os.path.exists(resume_line_file), f"Resume line PDF not found at {resume_line_file}")

    def test_overwrite_existing_pdf(self):
        """
        Test that generating a PDF correctly overwrites an existing file with the same name.

        This test verifies that the SimpleResumeGenerator properly handles the case
        where a PDF file with the same name already exists. The generator should
        remove the existing file and create a new one, ensuring no file conflicts
        or corruption occur during regeneration.

        :raises AssertionError: If the PDF file does not exist or is empty after overwrite.
        :rtype: None
        """
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
        """
        Clean up temporary files and directories after all tests have completed.

        This method removes the temporary folder and all its contents that were
        created during testing. It handles cleanup errors gracefully by catching
        exceptions and printing a warning instead of failing.

        :rtype: None
        """
        if os.path.exists(cls.tempFolder):
            try:
                shutil.rmtree(cls.tempFolder)
            except Exception as e:
                print(f"Warning: Could not clean up temp folder: {e}")















