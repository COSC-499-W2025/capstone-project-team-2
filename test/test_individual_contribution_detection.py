import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
from git import Actor, Repo

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))
import src.individual_contribution_detection as contribution_detection

def make_fake_extractor(mapping: dict, project_root: Path) -> MagicMock:
    """
    Create a fake FileMetadataExtractor-like object.

    mapping: dict of relative posix paths -> owner string (or None)
    project_root: Path used to compute relative paths from Path inputs
    """
    fake = MagicMock()

    def get_author(path):
        # Accept either Path or str
        p = Path(path)
        try:
            rel = p.relative_to(project_root).as_posix()
        except Exception:
            # fallback: try name only
            rel = p.name
        return mapping.get(rel)

    fake.get_author.side_effect = get_author
    return fake


class TestIndividualContributionDetection(unittest.TestCase):
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

    @patch('src.individual_contribution_detection.detect_project_type',
           return_value={"project_type": "individual", "mode": "local"})
    
    def test_non_collaborative_project_raises_error(self, _):
        """Non-collaborative projects should raise ValueError at entrypoint."""
        self._write("main.py", "print('Hello')")
        with self.assertRaises(ValueError) as ctx:
            contribution_detection.detect_individual_contributions(self.project_root)
        self.assertIn("not collaborative", str(ctx.exception).lower())

    def test_invalid_path_raises_error(self):
        """Invalid / missing paths raise ValueError."""
        invalid_path = self.project_root / "nonexistent"
        with self.assertRaises(ValueError) as ctx:
            contribution_detection.detect_individual_contributions(invalid_path)
        self.assertIn("does not exist", str(ctx.exception).lower())

    def test_local_collaborative_project_with_injected_extractor(self):
        """
        Test detect_individual_contributions_local with an injected fake extractor.
        This keeps tests deterministic and independent from OS file ownership.
        """
        # Prepare files and contributors file
        self._write("alice/file1.py", "print('a1')")
        self._write("bob/file2.py", "print('b1')")
        self._write("CONTRIBUTORS", "Alice\nBob")

        # Mapping: relative posix path -> owner
        mapping = {
            "alice/file1.py": "Alice",
            "bob/file2.py": "Bob",
        }

        fake_extractor = make_fake_extractor(mapping, self.project_root)

        result = contribution_detection.detect_individual_contributions_local(
            self.project_root, extractor=fake_extractor
        )

        # Strong assertions about contributors and files
        self.assertIn("Alice", result)
        self.assertIn("Bob", result)
        self.assertIn("alice/file1.py", result["Alice"]["files_owned"])
        self.assertIn("bob/file2.py", result["Bob"]["files_owned"])
        self.assertEqual(result["Alice"]["file_count"], 1)
        self.assertEqual(result["Bob"]["file_count"], 1)

    @patch('src.individual_contribution_detection.detect_project_type')
    @patch('src.individual_contribution_detection.FileMetadataExtractor')
    
    def test_entrypoint_uses_local_detector_with_patched_extractor(self, mock_extractor_cls, mock_detect):
        """
        Test the public entrypoint while patching FileMetadataExtractor so we don't rely on OS owners.
        """
        # create files and CONTRIBUTORS
        self._write("alice_a.py", "print('a')")
        self._write("bob_b.py", "print('b')")
        self._write("CONTRIBUTORS", "Alice\nBob")

        mock_detect.return_value = {"project_type": "collaborative", "mode": "local"}

        # fake extractor returns owners based on file name
        def _get_author(path):
            name = Path(path).name.lower()
            if "alice" in name:
                return "Alice"
            if "bob" in name:
                return "Bob"
            return None

        fake_instance = MagicMock()
        fake_instance.get_author.side_effect = _get_author
        mock_extractor_cls.return_value = fake_instance

        result = contribution_detection.detect_individual_contributions(self.project_root)

        self.assertTrue(result["is_collaborative"])
        self.assertEqual(result["mode"], "local")
        contributors = result["contributors"]
        self.assertIn("Alice", contributors)
        self.assertIn("Bob", contributors)
        self.assertIn("alice_a.py", contributors["Alice"]["files_owned"])
        self.assertIn("bob_b.py", contributors["Bob"]["files_owned"])

    def test_filename_inference_moves_unattributed(self):
        """
        If a file has no metadata owner but filename contains contributor token,
        it should be inferred and moved from <unattributed> to that contributor.
        """
        
        self._write("CONTRIBUTORS", "Alice")
        self._write("alice_utils.py", "print('util')")
        
        fake_extractor = make_fake_extractor({}, self.project_root)

        result = contribution_detection.detect_individual_contributions_local(
            self.project_root, extractor=fake_extractor
        )

        # Alice should receive the file via filename inference
        self.assertIn("Alice", result)
        self.assertIn("alice_utils.py", result["Alice"]["files_owned"])
        # Unattributed should be empty since alice_utils.py was inferred to Alice
        unattributed_count = result.get("<unattributed>", {}).get("file_count", 0)
        self.assertEqual(unattributed_count, 0, "alice_utils.py should be inferred to Alice, not remain unattributed")

    def test_unattributed_bucket_present_for_unknown_files(self):
        """
        Files with no metadata owner and no matching contributor names remain in <unattributed>.
        """
        self._write("orphan.py", "print('x')")
        fake_extractor = make_fake_extractor({}, self.project_root)
        result = contribution_detection.detect_individual_contributions_local(
            self.project_root, extractor=fake_extractor, include_unattributed=True
        )
        self.assertIn("<unattributed>", result)
        self.assertIn("orphan.py", result["<unattributed>"]["files_owned"])
        self.assertEqual(result["<unattributed>"]["file_count"], 1)
        
    @patch('src.individual_contribution_detection.detect_project_type')
    def test_git_multiple_distinct_authors(self, mock_detect):
        """
        Two different authors (different emails & different names) should be separate contributors.
        """
        mock_detect.return_value = {"project_type": "collaborative", "mode": "git"}

        repo = Repo.init(self.project_root)

        f1 = self._write("pa.py", "print('p')")
        repo.index.add([str(f1.relative_to(self.project_root))])
        a1 = Actor("Alice One", "alice1@example.com")
        repo.index.commit("add pa", author=a1, committer=a1)

        f2 = self._write("pb.py", "print('q')")
        repo.index.add([str(f2.relative_to(self.project_root))])
        a2 = Actor("Bob Two", "bob2@example.com")
        repo.index.commit("add pb", author=a2, committer=a2)

        result = contribution_detection.detect_individual_contributions(self.project_root)
        self.assertTrue(result["is_collaborative"])
        self.assertEqual(result["mode"], "git")
        contributors = result["contributors"]
        non_unat = [k for k in contributors.keys() if k != "<unattributed>"]
        # Expect two distinct contributors
        self.assertEqual(len(non_unat), 2)
        # Each should contain their respective file
        found_files = sum(("pa.py" in contributors[c]["files_owned"]) for c in non_unat)
        found_files += sum(("pb.py" in contributors[c]["files_owned"]) for c in non_unat)
        self.assertEqual(found_files, 2)


    @patch('src.individual_contribution_detection.detect_project_type')
    def test_git_untracked_file_becomes_unattributed(self, mock_detect):
        """
        A file that exists but was never committed should be reported as <unattributed>.
        """
        mock_detect.return_value = {"project_type": "collaborative", "mode": "git"}

        repo = Repo.init(self.project_root)

        # commit one file
        f1 = self._write("committed.py", "print('ok')")
        repo.index.add([str(f1.relative_to(self.project_root))])
        a = Actor("Committer", "c@example.com")
        repo.index.commit("commit", author=a, committer=a)

        # create an untracked file (do NOT add/commit)
        self._write("untracked_file.py", "print('untracked')")

        result = contribution_detection.detect_individual_contributions(self.project_root)
        contributors = result["contributors"]
        # Check untracked file ends up in <unattributed>
        self.assertIn("<unattributed>", contributors)
        self.assertIn("untracked_file.py", contributors["<unattributed>"]["files_owned"])


    @patch('src.individual_contribution_detection.detect_project_type')
    def test_git_subdirectory_files_tracked(self, mock_detect):
        """
        Files inside nested subdirectories should be attributed correctly.
        """
        mock_detect.return_value = {"project_type": "collaborative", "mode": "git"}

        repo = Repo.init(self.project_root)

        sub = self._write("src/utils/helpers.py", "print('h')")
        repo.index.add([str(sub.relative_to(self.project_root))])
        a = Actor("Helper", "helper@example.com")
        repo.index.commit("add helper", author=a, committer=a)

        result = contribution_detection.detect_individual_contributions(self.project_root)
        contributors = result["contributors"]
        non_unat = [k for k in contributors.keys() if k != "<unattributed>"]
        # Single contributor expected
        self.assertEqual(len(non_unat), 1)
        canon = non_unat[0]
        # Path should be posix relative 'src/utils/helpers.py'
        self.assertIn("src/utils/helpers.py", contributors[canon]["files_owned"])


    @patch('src.individual_contribution_detection.detect_project_type')
    def test_git_same_email_base_with_decorators_merged(self, mock_detect):
        """
        Email decorators (+ aliases like chris+one, chris+two) should be stripped,
        merging commits from the same base email address into one contributor.
        """
        mock_detect.return_value = {"project_type": "collaborative", "mode": "git"}

        repo = Repo.init(self.project_root)

        f1 = self._write("x1.py", "print('1')")
        repo.index.add([str(f1.relative_to(self.project_root))])
        # same display name with email decorator +one
        a1 = Actor("Chris", "chris+one@example.com")
        repo.index.commit("c1", author=a1, committer=a1)

        f2 = self._write("x2.py", "print('2')")
        repo.index.add([str(f2.relative_to(self.project_root))])
        # same display name with email decorator +two
        a2 = Actor("Chris", "chris+two@example.com")
        repo.index.commit("c2", author=a2, committer=a2)

        result = contribution_detection.detect_individual_contributions(self.project_root)
        contributors = result["contributors"]
        non_unat = [k for k in contributors.keys() if k != "<unattributed>"]
        # Should merge to 1 contributor since base email is the same (chris)
        self.assertEqual(len(non_unat), 1)
        canon = non_unat[0]
        self.assertIn("x1.py", contributors[canon]["files_owned"])
        self.assertIn("x2.py", contributors[canon]["files_owned"])


    @patch('src.individual_contribution_detection.detect_project_type')
    def test_git_merge_via_contributors_file(self, mock_detect):
        """
        If CONTRIBUTORS lists a canonical name, commits by different emails/names should map to that contributor.
        """
        mock_detect.return_value = {"project_type": "collaborative", "mode": "git"}

        # write CONTRIBUTORS so canonical name exists
        self._write("CONTRIBUTORS", "Sam Example")

        repo = Repo.init(self.project_root)

        f1 = self._write("a.py", "print('a')")
        repo.index.add([str(f1.relative_to(self.project_root))])
        # author uses short name with email1
        a1 = Actor("Sam", "sam+1@example.com")
        repo.index.commit("c1", author=a1, committer=a1)

        f2 = self._write("b.py", "print('b')")
        repo.index.add([str(f2.relative_to(self.project_root))])
        # author uses longer name with email2
        a2 = Actor("Sam Example", "sam+2@example.com")
        repo.index.commit("c2", author=a2, committer=a2)

        result = contribution_detection.detect_individual_contributions(self.project_root)
        contributors = result["contributors"]
        non_unat = [k for k in contributors.keys() if k != "<unattributed>"]
        # Because CONTRIBUTORS lists "Sam Example", both should be merged to a single canonical contributor
        self.assertEqual(len(non_unat), 1)
        canon = non_unat[0]
        self.assertIn("a.py", contributors[canon]["files_owned"])
        self.assertIn("b.py", contributors[canon]["files_owned"])

if __name__ == "__main__":
    unittest.main()
