import tempfile
import unittest
from pathlib import Path
import sys
from git import Repo, Actor

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))
import src.project_type_detection as project_type_detection

class TestProjectTypeDetection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()
  
    def _write(self, relative_path: str, content: str = "") -> Path:
        path = self.project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
    
    def test_extract_names_patterns(self):
        """Test that extract_names_from_text catches complex name patterns."""
        text = """
        Contributors:
        John Michael Doe
        Anne-Marie O'Connor
        McLovin
        D'Angelo
        """
        temp_file = self._write("AUTHORS", text)
        names = project_type_detection.extract_names_from_text(temp_file)
        expected = {"John Michael Doe", "Anne-Marie O'Connor", "McLovin", "D'Angelo"}
        self.assertTrue(expected.issubset(names))

    def test_individual_project_no_indicators(self):
        """A project with one file and default author should be 'individual'."""
        self._write("main.py", "print('Hello')")
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "individual", "mode": "local"})

    def test_collaborative_by_contributors_file(self):
        """Detect collaboration when CONTRIBUTORS file has multiple names."""
        self._write("CONTRIBUTORS", "John Doe\nJane Smith")
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "collaborative", "mode": "local"})

    def test_collaborative_by_authors_file(self):
        """Detect collaboration when AUTHORS file has multiple names."""
        self._write("AUTHORS", "John Doe\nJane Smith")
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "collaborative", "mode": "local"})

    def test_collaborative_by_readme_names(self):
        """Detect collaboration from multiple names in README.md."""
        self._write("README.md", "This project was built by Alice Brown and Bob Green.")
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "collaborative", "mode": "local"})

    def test_collaborative_by_metadata_authors(self):
        """Detect collaboration when multiple authors in metadata (mock)."""
        def fake_collect_authors(_root):
            return {"John", "Jane"}

        project_type_detection.collect_authors = fake_collect_authors
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "collaborative", "mode": "local"})

    def test_individual_by_single_author_metadata(self):
        """Detect individual project when only one author in metadata."""
        def fake_collect_authors(_root):
            return {"John"}

        project_type_detection.collect_authors = fake_collect_authors
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "individual", "mode": "local"})

    def test_combined_collaborative_signals(self):
        """Detect collaboration when both metadata and text indicators exist."""
        def fake_collect_authors(_root):
            return {"John", "Jane"}

        project_type_detection.collect_authors = fake_collect_authors
        self._write("CONTRIBUTORS", "John Doe\nJane Smith")

        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "collaborative", "mode": "local"})

    def test_unknown_for_invalid_path(self):
        """Return 'unknown' for invalid or non-existent folder."""
        invalid_path = self.project_root / "nonexistent"
        result = project_type_detection.detect_project_type(invalid_path)
        self.assertEqual(result, {"project_type": "unknown", "mode": "local"})
        
    def test_git_repo_individual(self):
        """Detect 'individual' from Git repo with one unique author."""
        repo = Repo.init(self.project_root)
        file_path = self._write("main.py", "print('hello')")

        # Add relative path (required by GitPython)
        relative_path = file_path.relative_to(self.project_root)
        repo.index.add([str(relative_path)])

        author = Actor("Alice", "alice@example.com")
        repo.index.commit("Initial commit", author=author, committer=author)

        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "individual", "mode": "git"})
        
    def test_git_repo_collaborative(self):
        """Detect 'collaborative' when multiple unique author names exist in Git repo."""
        repo = Repo.init(self.project_root)
        file_path = self._write("main.py", "print('v1')")
        relative_path = file_path.relative_to(self.project_root)
        repo.index.add([str(relative_path)])

        author1 = Actor("Alice", "alice@example.com")
        author2 = Actor("Bob", "bob@example.com")

        repo.index.commit("Initial commit", author=author1, committer=author1)
        file_path.write_text("print('v2')")
        repo.index.add([str(relative_path)])
        repo.index.commit("Second commit", author=author2, committer=author2)

        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "collaborative", "mode": "git"})

    def test_git_repo_empty(self):
        """Detect 'unknown' for empty Git repo (no commits)."""
        Repo.init(self.project_root)
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result, {"project_type": "unknown", "mode": "git"})

    def test_non_git_directory_fallback(self):
        """Ensure non-Git folders are handled gracefully."""
        self._write("main.py", "print('hi')")
        result = project_type_detection.detect_project_type(self.project_root)
        self.assertEqual(result["mode"], "local")
        self.assertIn(result["project_type"], ("individual", "collaborative", "unknown"))
    



if __name__ == "__main__":
    unittest.main()