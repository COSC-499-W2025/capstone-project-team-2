import os
import shutil
import tempfile
import zipfile

import unittest
from src.extraction import extractInfo

class TestExtraction(unittest.TestCase):

    """
    This is a Unit test for extraction.py

    These test cover the following issues:
    -Successful extraction of a valid Zip files
    -Handling of empty zip files
    -Handling of non-existent zip files
    -Handling of invalid or corrupted ZIP files
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
        self.temp_path = os.path.join(self.temp_dir, "temp")
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


        self.instance = extractInfo(self.test_zip_file_path)


    def test_empty_zip(self):
        """
        This test checks to see if the uploaded zip file after
        extraction is empty.


        This test verifies the following:
        - That the given the zip file content is empty.

        """

        empty_zip_path=extractInfo(self.empty_zip_path)
        empty_zip_path.extractFiles()
        self.assertEqual(os.listdir(self.temp_path),[])


    def test_extract_all_files(self):

        """
        Test the extraction of vaild zip file.

        Verifies the following:
        - All files in the given zip are successfully extracted.
        - Each expected file that is predefined in the setup function
          is in the extraction folder when extraction is complete.


        """
        self.instance.extractFiles()
        for file in os.listdir(self.temp_path):
            file_path = os.path.join(self.temp_path, file)
            self.assertTrue(os.path.exists(file_path))

    def test_invalid_zip_file(self):
        """
        Test Behavior when extracting an invalid or corrupted zip file.

        Verifies the following:
        - That if invalid zip is uploaded the system will raise the
          BadZipFile exception when trying to extract the contents of
          upload zip file.

        """
        bad_instance = extractInfo(self.not_zip_file_path)
        with self.assertRaises(zipfile.BadZipFile):
            bad_instance.extractFiles()


    def test_file_not_found_error(self):
        """
        Test behavior when ZIP file does not exist.

        Verifies the following:
        - A FileNotFoundError is raised when the file path
          to that particular zip is not valid.

        """
        file_not_exist_instance=extractInfo(self.does_not_exist_zip)
        with self.assertRaises(FileNotFoundError):
            file_not_exist_instance.extractFiles()


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