import os
import shutil
import sys
import unittest
import getpass
import tempfile
import pytest

from pathlib import Path
from io import StringIO
from unittest.mock import patch
import pytest

from src.core.data_extraction import FileMetadataExtractor

class TestDataExtract(unittest.TestCase):
    """
    Unit test suite for validating the behavior of the FileMetadataExtractor
    class, including directory traversal, metadata extraction, and
    cross-platform author resolution.
    """

    def setUp(self):
        """
        Create a temporary directory used as a sandbox for filesystem tests.

        Args:
            None: This method does not take any parameters.

        Returns:
            None: This method prepares test state before each test runs.
        """
        self.temp_dir = Path(tempfile.mkdtemp())


    def test_tree(self):
        """
        Verify that file_hierarchy correctly detects files in a non-empty
        directory and includes them in the returned tree structure.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """

        # create temporary files and directory for testing
        file_path=self.temp_dir / "file.txt"
        file_path.write_text("This is a test file")


        """
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir / "file.txt"
        test_file.touch()
        """

        try:
            extractor = FileMetadataExtractor(self.temp_dir)
            tree_data = extractor.file_hierarchy()

            # Get all file names in root directory
            children_names = [c["name"] for c in tree_data.get("children", [])]


            # Assert that "file.txt" exists
            self.assertIn("file.txt", children_names)
        finally:
            # if files and directory exist remove them after test
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)



    def test_tree_empty(self):
        """
        Verify that an empty directory is correctly identified and represented
        with a placeholder child node indicating emptiness.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """

        temp_dir = Path("empty_temp")
        temp_dir.mkdir(exist_ok=True)

        try:
            extractor = FileMetadataExtractor(temp_dir)
            tree_data = extractor.file_hierarchy()
            children = tree_data.get("children", [])

            # Expect a single child with name "Empty"
            children = tree_data.get("children", [])
            self.assertEqual(len(children), 1)
            self.assertEqual(children[0]["name"], "Empty")
        finally:
            # if directory exist remove them after test
            if temp_dir.exists():
                temp_dir.rmdir()


    def test_file_hierarchy_nonexistent_path(self):
        """
        Verify that attempting to generate a hierarchy for a non-existent path
        raises FileNotFoundError.
        """
        test_path = Path("does_not_exist")
        extractor = FileMetadataExtractor(test_path)

        with self.assertRaises(FileNotFoundError) as context:
            extractor.file_hierarchy()
        
        self.assertIn("not found", str(context.exception).lower())

    def test_file_hierarchy_not_a_directory(self):
        """
        Verify that attempting to generate a hierarchy for a path that exists
        but is not a directory raises ValueError.
        """
        temp_file = Path("not_a_dir.txt")
        temp_file.write_text("data")

        try:
            extractor = FileMetadataExtractor(temp_file)
            
            with self.assertRaises(ValueError) as context:
                extractor.file_hierarchy()
            
            self.assertIn("not a directory", str(context.exception).lower())
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @patch("platform.system", return_value="Windows")
    @patch("win32security.LookupAccountSid")
    @patch("win32security.GetFileSecurity")
    @pytest.mark.skipif(sys.platform != "win32", reason="win32security is only available on Windows")
    @unittest.skipUnless(sys.platform == "win32", "Requires Windows win32 APIs")
    def test_win32(self, moc_get_sec, mock_lookup, mock_system):
        """
        Verify that file author resolution correctly uses Win32 security APIs
        when running on a Windows system with win32security available.

        Args:
            moc_get_sec: Mocked GetFileSecurity function.
            mock_lookup: Mocked LookupAccountSid function.
            mock_system: Mocked platform.system return value.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # creating a mock file author and testing the return with win32
        mock_lookup.return_value = ("John", "DESKTOP-12345", 1)
        extractor = FileMetadataExtractor("test/path")
        author = extractor.get_author(Path("file.txt"))
        self.assertEqual(author, "John")

    @patch("platform.system", return_value="Windows")
    def test_no_win32(self, mock_system):
        """
        Verify that file author resolution falls back to the current system user
        when running on Windows without win32security available.

        Args:
            mock_system: Mocked platform.system return value.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Testing system output when Win32 is not installed
        with patch("src.core.data_extraction.win32security", None):
            with patch("getpass.getuser", return_value="FallbackUser"):
                extractor = FileMetadataExtractor("test/path")
                author = extractor.get_author(Path("file.txt"))
                # tests for the fallback user (computer owner)
                self.assertEqual(author, "FallbackUser")

    @patch("platform.system", return_value="Darwin")
    def test_MacOs(self, mock_system):
        """
        Verify that file author resolution on macOS systems falls back to the
        current logged-in user.

        Args:
            mock_system: Mocked platform.system return value.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        extractor = FileMetadataExtractor("test/path")
        author = extractor.get_author(Path("file.txt"))
        self.assertEqual(author, getpass.getuser())


if __name__ == "__main__":
    unittest.main()
