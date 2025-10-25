import os
import sys
import unittest
import getpass

from pathlib import Path
from io import StringIO
from unittest.mock import patch

from src.data_extraction import FileMetadataExtractor

class TestDataExtract(unittest.TestCase):

    def test_tree(self):

        # create temporary files and directory for testing
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir / "file.txt"
        test_file.touch()

        try:
            extractor = FileMetadataExtractor(temp_dir)
            result = list(extractor.tree(temp_dir))
            self.assertIn("`-- file.txt", result[-1])
        finally:
            # if files and directory exist remove them after test
            if test_file.exists():
                test_file.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()

    def test_tree_empty(self):
        temp_dir = Path("empty_temp")
        temp_dir.mkdir(exist_ok=True)

        try:
            extractor = FileMetadataExtractor(temp_dir)
            result = list(extractor.tree(temp_dir))
            self.assertEqual(result, [" Empty"])
        finally:
            # if directory exist remove them after test
            if temp_dir.exists():
                temp_dir.rmdir()


    def test_file_hierarchy_nonexistent_path(self):
        # creates a bad dummy path
        test_path = Path("does_not_exist")
        extractor = FileMetadataExtractor(test_path)

        with patch("sys.stdout", new=StringIO()) as test_out:
            extractor.file_hierarchy()
            output = test_out.getvalue()

        self.assertIn("Error: Filepath not found", output)

    def test_file_hierarchy_not_a_directory(self):
        temp_file = Path("not_a_dir.txt")
        temp_file.write_text("data")
        

        try:
            extractor = FileMetadataExtractor(temp_file)
            with patch("sys.stdout", new=StringIO()) as test_out:
                extractor.file_hierarchy()
                output = test_out.getvalue()

            self.assertIn("Error: File is not a directory", output)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @patch("platform.system", return_value="Windows")
    @patch("win32security.LookupAccountSid")
    @patch("win32security.GetFileSecurity")
    def test_win32(self, moc_get_sec, mock_lookup, mock_system):
        # creating a mock file author and testing the return with win32
        mock_lookup.return_value = ("John", "DESKTOP-12345", 1)
        extractor = FileMetadataExtractor("test/path")
        author = extractor.get_author(Path("file.txt"))
        self.assertEqual(author, "John")

    @patch("platform.system", return_value="Windows")
    def test_no_win32(self, mock_system):
        # Testing system output when Win32 is not installed
        with patch("src.data_extraction.win32security", None):
            with patch("getpass.getuser", return_value="FallbackUser"):
                extractor = FileMetadataExtractor("test/path")
                author = extractor.get_author(Path("file.txt"))
                # tests for the fallback user (computer owner)
                self.assertEqual(author, "FallbackUser")

    @patch("platform.system", return_value="Darwin")
    def test_MacOs(self, mock_system):
            extractor = FileMetadataExtractor("test/path")
            author = extractor.get_author(Path("file.txt"))
            self.assertEqual(author, getpass.getuser())


if __name__ == "__main__":
    unittest.main()
