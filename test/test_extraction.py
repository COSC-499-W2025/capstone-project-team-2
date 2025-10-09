import os
import shutil
import tempfile
import zipfile

import unittest
from src.extraction import extractInfo

class TestExtraction(unittest.TestCase):


    def setUp(self):
        self.sample_files={"file1.txt":"Content 1","file2.txt":"Content 2","file3.txt":"Content 3"}
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        self.test_zip_file_path = os.path.join(self.temp_dir, "test.zip")
        with zipfile.ZipFile(self.test_zip_file_path, "w") as zf:
            for key,value in self.sample_files.items():
                zf.writestr(key,value)


        self.instance = extractInfo(self.test_zip_file_path)


    def tearDown(self):
        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


    def test_extract_all_files(self):
        self.instance.extractFiles()
        temp_path = os.path.join(self.temp_dir, "temp")
        for file in os.listdir(temp_path):
            file_path = os.path.join(temp_path, file)
            self.assertTrue(os.path.exists(file_path))








if __name__== "__main__":
    unittest.main()