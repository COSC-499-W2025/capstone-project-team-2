import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch
import logging

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))
from src.contribution_skill_association import (
    associate_contribution_skills,
    get_skills_for_file_subset,
    dedupe_ordered,
    stable_unique_sorted,
    clear_skills_cache,
    skills_cache
)

class TestContributionSkills(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        clear_skills_cache()
        logging.disable(logging.CRITICAL)  

    def tearDown(self):
        self.temp_dir.cleanup()
        clear_skills_cache()
        logging.disable(logging.NOTSET)

    def _write(self, relative_path: str, content: str = "") -> Path:
        """Helper to create files in the test project."""
        path = self.project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    @patch('src.contribution_skill_association.detect_individual_contributions')
    def test_non_collaborative_project_returns_empty(self, mock_detect):
        """Non-collaborative projects should return empty structure."""
        mock_detect.return_value = {
            "is_collaborative": False,
            "contributors": {}
        }
        
        self._write("main.py", "print('hello')")
        
        result = associate_contribution_skills(self.project_root)
        
        self.assertEqual(result["project_skills"], [])
        self.assertEqual(result["contributors"], {})

    @patch('src.contribution_skill_association.detect_individual_contributions')
    @patch('src.contribution_skill_association.identify_skills')
    def test_multiple_contributors_different_skills(self, mock_identify, mock_detect):
        """Multiple contributors with different file types should get different skills."""
        mock_detect.return_value = {
            "is_collaborative": True,
            "contributors": {
                "Alice": {
                    "files_owned": ["main.py"],
                    "file_count": 1
                },
                "Bob": {
                    "files_owned": ["app.js"],
                    "file_count": 1
                }
            }
        }
        
        def skill_detector(root):
            files = [f.name for f in root.rglob("*") if f.is_file()]
            if "main.py" in files:
                return ["Python"]
            elif "app.js" in files:
                return ["JavaScript"]
            return []
        
        mock_identify.side_effect = skill_detector
        
        self._write("main.py", "print('hello')")
        self._write("app.js", "console.log('hello')")
        
        result = associate_contribution_skills(self.project_root)
        
        self.assertIn("Alice", result["contributors"])
        self.assertIn("Bob", result["contributors"])
        self.assertEqual(result["contributors"]["Alice"]["skills"], ["Python"])
        self.assertEqual(result["contributors"]["Bob"]["skills"], ["JavaScript"])

    @patch('src.contribution_skill_association.detect_individual_contributions')
    @patch('src.contribution_skill_association.identify_skills')
    def test_project_skills_vs_contributor_skills(self, mock_identify, mock_detect):
        """Project-wide skills should differ from individual contributor skills."""
        mock_detect.return_value = {
            "is_collaborative": True,
            "contributors": {
                "Alice": {
                    "files_owned": ["main.py"],
                    "file_count": 1
                }
            }
        }
        
        # Project has more skills than individual contributor
        def skill_detector(root):
            files = [f.name for f in root.rglob("*") if f.is_file()]
            if len(files) > 1:  # Project-wide call
                return ["Python", "JavaScript", "Docker"]
            else:  # Individual contributor call
                return ["Python"]
        
        mock_identify.side_effect = skill_detector
        
        self._write("main.py", "print('hello')")
        self._write("app.js", "console.log('hello')")
        self._write("Dockerfile", "FROM python:3.9")
        
        result = associate_contribution_skills(self.project_root)
        
        # Project has all skills
        self.assertEqual(len(result["project_skills"]), 3)
        # Alice only has Python
        self.assertEqual(result["contributors"]["Alice"]["skills"], ["Python"])

    @patch('src.contribution_skill_association.identify_skills')
    def test_caching_behavior(self, mock_identify):
        """Same file set should use cached results."""
        mock_identify.return_value = ["Python"]
        
        self._write("main.py", "print('hello')")
        
        files = ["main.py"]
        
        # First call - populates cache
        result1 = get_skills_for_file_subset(self.project_root, files)
        cache_size_after_first = len(skills_cache)
        
        # Second call - should use cache
        result2 = get_skills_for_file_subset(self.project_root, files)
        cache_size_after_second = len(skills_cache)
        
        self.assertEqual(result1, result2)
        self.assertEqual(cache_size_after_first, cache_size_after_second)
        # Cache should have one entry
        self.assertEqual(len(skills_cache), 1)

    def test_clear_skills_cache(self):
        """clear_skills_cache should empty the cache."""
        skills_cache[("file1.py",)] = ["Python"]
        self.assertEqual(len(skills_cache), 1)
        
        clear_skills_cache()
        self.assertEqual(len(skills_cache), 0)

    @patch('src.contribution_skill_association.detect_individual_contributions')
    @patch('src.contribution_skill_association.identify_skills')
    def test_empty_and_duplicate_files(self, mock_identify, mock_detect):
        """Should handle empty file lists and deduplicates."""
        mock_detect.return_value = {
            "is_collaborative": True,
            "contributors": {
                "Alice": {
                    "files_owned": ["main.py", "main.py", "utils.py"],  # Duplicates
                    "file_count": 3
                },
                "Bob": {
                    "files_owned": [],  # Empty
                    "file_count": 0
                }
            }
        }
        
        mock_identify.return_value = ["Python"]
        
        self._write("main.py", "print('hello')")
        self._write("utils.py", "def func(): pass")
        
        result = associate_contribution_skills(self.project_root)
        
        # Alice's duplicates should be removed
        self.assertEqual(result["contributors"]["Alice"]["file_count"], 2)
        # Bob with no files
        self.assertEqual(result["contributors"]["Bob"]["file_count"], 0)
        self.assertEqual(result["contributors"]["Bob"]["skills"], [])

    @patch('src.contribution_skill_association.detect_individual_contributions')
    @patch('src.contribution_skill_association.identify_skills')
    def test_missing_files_and_exceptions(self, mock_identify, mock_detect):
        """Should handle missing files and identify_skills exceptions gracefully."""
        mock_detect.return_value = {
            "is_collaborative": True,
            "contributors": {
                "Alice": {
                    "files_owned": ["main.py", "nonexistent.py"],
                    "file_count": 2
                }
            }
        }
        
        # First call succeeds (project-wide), second call fails (contributor)
        mock_identify.side_effect = [["Python"], Exception("Skill detection failed")]
        
        self._write("main.py", "print('hello')")
        # nonexistent.py is NOT created
        
        # Should not crash
        result = associate_contribution_skills(self.project_root)
        
        self.assertIn("Alice", result["contributors"])
        # Should handle exception gracefully
        self.assertEqual(result["contributors"]["Alice"]["skills"], [])

    @patch('src.contribution_skill_association.detect_individual_contributions')
    @patch('src.contribution_skill_association.identify_skills')
    def test_duplicate_skills_and_none_handling(self, mock_identify, mock_detect):
        """Should deduplicate and sort skills, handle None returns."""
        mock_detect.return_value = {
            "is_collaborative": True,
            "contributors": {
                "Alice": {
                    "files_owned": ["main.py"],
                    "file_count": 1
                },
                "Bob": {
                    "files_owned": ["app.js"],
                    "file_count": 1
                }
            }
        }
        
        # Alice gets duplicate skills, Bob gets None
        mock_identify.side_effect = [
            ["Python", "Testing", "Python", "Flask"],  # Project-wide with duplicates
            ["Python", "Testing", "Python", "Flask"],  # Alice with duplicates
            None  # Bob gets None
        ]
        
        self._write("main.py", "print('hello')")
        self._write("app.js", "console.log('hello')")
        
        result = associate_contribution_skills(self.project_root)
        
        # Alice's skills should be deduplicated and sorted
        alice_skills = result["contributors"]["Alice"]["skills"]
        self.assertEqual(alice_skills, ["Flask", "Python", "Testing"])
        self.assertEqual(len(alice_skills), len(set(alice_skills)))  # No duplicates
        
        # Bob should handle None gracefully
        self.assertEqual(result["contributors"]["Bob"]["skills"], [])

    def test_dedupe_ordered(self):
        """dedupe_ordered should remove duplicates while preserving order."""
        items = ["a", "b", "a", "c", "b", "d"]
        result = dedupe_ordered(items)
        self.assertEqual(result, ["a", "b", "c", "d"])
        
        # Test empty list
        self.assertEqual(dedupe_ordered([]), [])

    def test_stable_unique_sorted(self):
        """stable_unique_sorted should return unique items sorted alphabetically."""
        items = ["python", "javascript", "python", "go"]
        result = stable_unique_sorted(items)
        self.assertEqual(result, ["go", "javascript", "python"])
        
        # Test empty list
        self.assertEqual(stable_unique_sorted([]), [])

    @patch('src.contribution_skill_association.detect_individual_contributions')
    @patch('src.contribution_skill_association.identify_skills')
    def test_nested_directories_and_posix_paths(self, mock_identify, mock_detect):
        """Should handle nested directories and POSIX paths correctly."""
        mock_detect.return_value = {
            "is_collaborative": True,
            "contributors": {
                "Alice": {
                    "files_owned": ["src/utils/helper.py", "tests/test_main.py"],  # POSIX format
                    "file_count": 2
                }
            }
        }
        
        mock_identify.return_value = ["Python", "Testing"]
        
        self._write("src/utils/helper.py", "def helper(): pass")
        self._write("tests/test_main.py", "def test_main(): pass")
        
        # Should work on all OS
        result = associate_contribution_skills(self.project_root)
        
        self.assertIn("Alice", result["contributors"])
        self.assertEqual(result["contributors"]["Alice"]["file_count"], 2)
        self.assertIn("Python", result["contributors"]["Alice"]["skills"])

if __name__ == "__main__":
    unittest.main()