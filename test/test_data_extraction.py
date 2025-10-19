import os
import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
