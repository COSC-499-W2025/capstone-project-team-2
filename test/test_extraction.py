import os
import shutil
import tempfile
import zipfile

import unittest
from src.extraction import extractInfo

class TestExtraction(unittest.TestCase):

    """
    Here I am using one of builtin function python unitTest library which run at the start of the test where in this case
    it creates a random  folder and switches to that directory that it creates a
    new zip fle and saves it inside the created temporary folder. and instantiate our extractInfo class from extraction.py

    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)



        self.test_zip_file_path = os.path.join(self.test_dir, "test.zip")
        with zipfile.ZipFile(self.test_zip_file_path, "w") as zf:
            zf.writestr("file1.txt", "Content 1")
            zf.writestr("file2.txt", "Content 2")
            zf.writestr("file3.txt", "Content 3")

        self.instance = extractInfo(self.test_zip_file_path)



    """
    This is another built in function of unit test where when the test is complete it will peform this function 
    which in this case is design to clear/remove the temporary created folder from os.mkdtemp()
    """
    def tearDown(self):
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)


    """
    Here we run the actual test to see if the zip folder has been extracted successfully 
    """
    def test_extract_all_files(self):
        self.instance.extractFiles()
        temp_path = os.path.join(self.test_dir, "temp")
        self.assertTrue(os.path.exists(os.path.join(temp_path, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(temp_path, "file2.txt")))
        self.assertTrue(os.path.exists(os.path.join(temp_path, "file3.txt")))



if __name__== "__main__":
    unittest.main()