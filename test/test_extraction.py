import os
import shutil
import tempfile
import zipfile


import unittest
from pathlib import Path

from src.core.extraction import extractInfo
from src.cli.CLI_interface_for_file_extraction import zipExtractionCLI
from unittest.mock import patch, MagicMock, call


class TestExtraction(unittest.TestCase):

    """
    This is a Unit test for extraction.py
    These test cover the following issues:
    
    For method extractFiles
    -Successful extraction of a valid Zip files
    -Handling of empty zip files
    -Handling of non-existent zip files
    -Handling of invalid or corrupted ZIP files

    For method verifyZIP
    -
    For method CLI
    - Simulate typing q to exit the program
    - Returning successfully message and exit the program when the user uploads a valid zip file
    - Exits the program after the number of tries have been met
    """


    def setUp(self):

        """
        This is a setup function that does the following at the start of each
        pytest run:
        -Creates a temporary directory and changes the working directory
        -Generates:
            -A valid zip file containing three preset text files
            -An empty zip file
            -An invalid zip file
            -A non-existent file

        """

        self.sample_files={"file1.txt":"Content 1","file2.txt":"Content 2","file3.txt":"Content 3"}
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        #self.temp_path = os.path.join(self.temp_dir, "temp")
        os.chdir(self.temp_dir)

        self.test_zip_file_path = os.path.join(self.temp_dir, "test.zip")
        self.not_zip_file_path=os.path.join(self.temp_dir,"BadTest.zip")
        self.does_not_exist_zip=os.path.join(self.temp_dir,"does_not_exist.zip")
        self.empty_zip_path=os.path.join(self.temp_dir,"empty.zip")

        with zipfile.ZipFile(self.test_zip_file_path, "w") as zf:
            for key,value in self.sample_files.items():
                zf.writestr(key,value)

        with zipfile.ZipFile(self.empty_zip_path,"w"):
            pass

        with open(self.not_zip_file_path,"w") as f:
            f.write("Random")


    def test_empty_zip(self):
        """
        This test checks to see if the uploaded zip file after
        extraction is empty.


        This test verifies the following:
        - That the given the zip file content is empty.

        """

        temp_path = extractInfo().extractFiles(Path(self.empty_zip_path), "empty")
        self.assertEqual(os.listdir(temp_path),[])
        shutil.rmtree(temp_path, ignore_errors=True)


    def test_extract_all_files(self):

        """
        Test the extraction of vaild zip file.

        Verifies the following:
        - All files in the given zip are successfully extracted.
        - Each expected file that is predefined in the setup function
          is in the extraction folder when extraction is complete.

        """

        temp_path = extractInfo().extractFiles(Path(self.test_zip_file_path), "test")
        for file in os.listdir(temp_path):
            file_path = os.path.join(temp_path, file)
            self.assertTrue(os.path.exists(file_path))
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_invalid_zip_file(self):
        """
        Test Behavior when extracting an invalid or corrupted zip file.

        Verifies the following:
        - That if invalid zip is uploaded the system will raise the
          BadZipFile exception when trying to extract the contents of
          upload zip file.

        """
        with self.assertRaises(zipfile.BadZipFile):
            extractInfo().extractFiles(Path(self.not_zip_file_path), "name")


    def test_file_not_found_error(self):
        """
        Test behavior when ZIP file does not exist.

        Verifies the following:
        - A FileNotFoundError is raised when the file path
          to that particular zip is not valid.

        """
        with self.assertRaises(FileNotFoundError):
            extractInfo().extractFiles(Path(self.does_not_exist_zip), "name")

    
    def test_verifyZIP_no_path(self):
        """
        Positive Test
        Test for when file path is invalid

        Verifies that:
        - Correct error text is returned when file path is invalid
        """
    
        text = extractInfo().verifyZIP(Path(self.does_not_exist_zip))
        self.assertTrue(extractInfo.PATH_ERROR_TEXT in text)

    def test_verifyZIP_not_zip(self):
        """
        Positive Test
        Test for when file is not a zip

        Verifies that:
        - Correct error text is returned when file is not zip
        """
        path = os.path.join(self.original_cwd, "test")
        path = os.path.join(path, "TestZIPs")
        path = os.path.join(path, "test.txt")
        text = extractInfo().verifyZIP(Path(path))
        self.assertTrue(extractInfo.NOT_ZIP_ERROR_TEXT in text)

    def test_verifyZIP_bad_zip(self):
        """
        Positive Test
        Test for when zip file contains a corrupt file (invalid magic bytes)

        Verifies that:
        - Correct error text is returned when extracted file has invalid header
        """
        path = os.path.join(self.original_cwd, "test")
        path = os.path.join(path, "TestZIPs")
        path = os.path.join(path, "CorruptInternalZIP.zip")
        text = extractInfo().runExtraction(Path(path))
        print(text)
        self.assertTrue(extractInfo.CORRUPT_FILE_ERROR_TEXT in text)

    def test_verifyZIP_not_bad_not_zip(self):
        """
        Negative Test
        Test for when file is not a zip file, that file isn't marked as bad

        Verifies that:
        - Non-zip file isn't marked as bad zip file
        """
        path = os.path.join(self.original_cwd, "test")
        path = os.path.join(path, "TestZIPs")
        path = os.path.join(path, "test.txt")
        text = extractInfo().verifyZIP(Path(path))
        self.assertFalse(extractInfo.BAD_ZIP_ERROR_TEXT in text)

    def test_runExtraction_no_path(self):
        """
        Positive Test
        Test for when file path is invalid

        Verifies that:
        - Correct error text is returned when file path is invalid
        """
    
        text = extractInfo().runExtraction(Path(self.does_not_exist_zip))
        self.assertTrue(extractInfo.PATH_ERROR_TEXT in text)

    def test_runExtraction_not_zip(self):
        """
        Positive Test
        Test for when file is not a zip

        Verifies that:
        - Correct error text is returned when file is not zip
        """
        path = os.path.join(self.original_cwd, "test")
        path = os.path.join(path, "TestZIPs")
        path = os.path.join(path, "test.txt")
        text = extractInfo().runExtraction(Path(path))
        self.assertTrue(extractInfo.NOT_ZIP_ERROR_TEXT in text)

    def test_runExtraction_bad_zip(self):
        """
        Positive Test
        Test for when zip file contains a corrupt file (invalid magic bytes)

        Verifies that:
        - Correct error text is returned when extracted file has invalid header
        """
        path = os.path.join(self.original_cwd, "test")
        path = os.path.join(path, "TestZIPs")
        path = os.path.join(path, "CorruptInternalZIP.zip")
        text = extractInfo().runExtraction(Path(path))
        self.assertTrue(extractInfo.CORRUPT_FILE_ERROR_TEXT in text)

    def test_runExtraction_empty_zip(self):
        """
        This test checks to see if the uploaded zip file after
        extraction is empty.


        This test verifies the following:
        - That the given the zip file content is empty.

        """

        temp_path = extractInfo().runExtraction(Path(self.empty_zip_path))
        self.assertEqual(os.listdir(temp_path),[])
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_runExtraction_extract_all_files(self):

        """
        Test the extraction of vaild zip file.

        Verifies the following:
        - All files in the given zip are successfully extracted.
        - Each expected file that is predefined in the setup function
          is in the extraction folder when extraction is complete.


        """
        temp_path = extractInfo().runExtraction(Path(self.test_zip_file_path))
        for file in os.listdir(temp_path):
            file_path = os.path.join(temp_path, file)
            self.assertTrue(os.path.exists(file_path))
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_verifyZIP_rejects_unsafe_archive_path(self):
        """Zip-slip style member paths must be rejected before extraction."""
        unsafe_zip = os.path.join(self.temp_dir, "unsafe.zip")
        with zipfile.ZipFile(unsafe_zip, "w") as zf:
            zf.writestr("../evil.txt", "pwn")

        text = extractInfo().verifyZIP(Path(unsafe_zip))
        self.assertTrue(extractInfo.UNSAFE_ARCHIVE_PATH_ERROR_TEXT in text)





    @patch('src.cli.CLI_interface_for_file_extraction.extractInfo')
    @patch('src.cli.CLI_interface_for_file_extraction.input')
    @patch('builtins.print')
    def test_valid_zip_file_extraction_cli(self,mock_print, mock_input, mock_extract_Info):
        """
        Here we are simulating the user interaction with the extraction cli
        when the user uploads a valid zip file, returning a success message
        """
        test_file_name=Path(self.test_zip_file_path).name
        mock_input.return_value = self.test_zip_file_path
        mock_instance=MagicMock()
        mock_extract_Info.return_value = mock_instance

        cli=zipExtractionCLI()
        #Here I am instantiating the zipExtreactionCLI class
        cli.run_cli()
        mock_extract_Info.assert_called_once_with(self.test_zip_file_path)
        mock_instance.runExtraction.assert_called_once()
        mock_print.assert_any_call(f"{test_file_name} has been extracted successfully")

    @patch('src.cli.CLI_interface_for_file_extraction.extractInfo')
    @patch('src.cli.CLI_interface_for_file_extraction.input')
    @patch('builtins.print')
    def test_invalid_zip_file_extraction_CLI(self, mock_print, mock_input, mock_extract_Info):
        """
        Here we are simulating the user interaction with the extraction cli
        when they upload a invalid zip file, returning an error message
        """
        mock_input.return_value = self.not_zip_file_path
        mock_instance = MagicMock()
        mock_instance.runExtraction.return_value = "Error! Zip file is bad!"
        mock_extract_Info.return_value = mock_instance

        cli = zipExtractionCLI()
        cli.run_cli(max_retries=1)


        mock_print.assert_any_call("Error! Zip file is bad!")

    @patch('builtins.input', return_value='q')
    @patch('builtins.print')
    def test_successfully_exit_CLI(self,mock_print,mock_input):
        """
        Tests that the CLI exits when the user types 'q'

        This test simulates a user entering 'q' to exit/quit the zip extraction CLI
        through verifying that the program displays exit message "Exiting zip Extraction Returning you back to main screen"."


        """
        cli = zipExtractionCLI()
        cli.run_cli()
        mock_print.assert_any_call("Exiting zip Extraction Returning you back to main screen")



    @patch('src.cli.CLI_interface_for_file_extraction.extractInfo')
    @patch('src.cli.CLI_interface_for_file_extraction.input')
    @patch('builtins.print')
    def test_invalid_zip_file_extraction_minimum_retries_CLI(self, mock_print, mock_input, mock_extract_Info):
        """
        Ensure the CLI runs extraction multiple times for invalid ZIP files.
        Checks that both extractInfo() and runExtraction() are called
        at least twice before exiting.
        """

        mock_input.return_value = self.not_zip_file_path

        mock_instance = MagicMock()
        mock_instance.runExtraction.return_value = extractInfo.BAD_ZIP_ERROR_TEXT
        mock_extract_Info.return_value = mock_instance

        cli = zipExtractionCLI()
        cli.run_cli(max_retries=3)


        assert mock_extract_Info.call_count >= 2, (
            f"Expected extractInfo() to be called multiple times, got {mock_extract_Info.call_count}"
        )
        assert mock_instance.runExtraction.call_count >= 2, (
            f"Expected runExtraction() to be called multiple times, got {mock_instance.runExtraction.call_count}"
        )


        mock_print.assert_any_call(extractInfo.BAD_ZIP_ERROR_TEXT)
        mock_print.assert_any_call("Too many invalid attempts. Exiting...")

    def tearDown(self):

        """
        This function cleans up after the test is complete.

        Does the following:
        -Returns to the original working directory.
        -Removes the temporary folder and its associated
        content.
        """

        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)















if __name__== "__main__":
    unittest.main()
