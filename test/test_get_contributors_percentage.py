from pathlib import Path
import shutil
from src.get_contributors_percentage_per_person import get_contributors_percentages_git
import unittest
import tempfile
from git import Repo, Actor
from github import Github, Auth
import os
from dotenv import load_dotenv
import uuid


class TestIndividualContributionDetection_percentage_git(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs ONCE for the whole class.
        Creates 2 local repos + 2 GitHub repos and pushes to them.
        """
        load_dotenv()
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise unittest.SkipTest("GITHUB_TOKEN not set; skipping GitHub integration tests")

        cls.token = token

        # --- local repos (temp dirs) ---
        cls.repo_path = tempfile.mkdtemp()
        cls.repo_path_2 = tempfile.mkdtemp()

        cls.repo = Repo.init(cls.repo_path)
        cls.repo_2 = Repo.init(cls.repo_path_2)

        file_path = os.path.join(cls.repo_path, "file.txt")
        file_path_2 = os.path.join(cls.repo_path, "file2.txt")

        with open(file_path, "w") as f:
            f.write("Hello 1")

        with open(file_path_2, "w") as f:
            f.write("Hello 2")

        # repo_2: 1 commit by Bob
        cls.repo_2.git.add(A=True)
        cls.repo_2.index.commit("Commit 1", author=Actor("Bob", "Bob@example.com"))

        # repo: Commit A (Alice)
        cls.repo.git.add(A=True)
        cls.repo.index.commit("Commit A", author=Actor("Alice", "alice@example.com"))

        # modify file and Commit B (Bob)
        with open(file_path, "a") as f:
            f.write("Hello 2")

        cls.repo.git.add(A=True)
        cls.repo.index.commit("Commit B", author=Actor("Bob", "bob@example.com"))

        # --- GitHub setup (once) ---
        auth = Auth.Token(cls.token)
        cls.gh = Github(auth=auth)
        user = cls.gh.get_user()

        repo_name = f"test-repo-temp-{uuid.uuid4().hex[:8]}"
        repo_name_2 = f"test-repo-temp-2-{uuid.uuid4().hex[:8]}"

        cls.remote_repo = user.create_repo(
            name=repo_name,
            private=False,
        )
        cls.remote_repo_2 = user.create_repo(
            name=repo_name_2,
            private=False,
        )

        # set up remotes & push current branch (don’t hard-code "master")
        remote_url_1 = cls.remote_repo.clone_url.replace(
            "https://",
            f"https://{cls.token}@"
        )
        cls.repo.create_remote("origin", remote_url_1)
        branch_1 = cls.repo.active_branch.name
        cls.repo.git.push("--set-upstream", "origin", branch_1)

        remote_url_2 = cls.remote_repo_2.clone_url.replace(
            "https://",
            f"https://{cls.token}@"
        )
        cls.repo_2.create_remote("origin", remote_url_2)
        branch_2 = cls.repo_2.active_branch.name
        cls.repo_2.git.push("--set-upstream", "origin", branch_2)

    # ----------------- tests -----------------

    def test_two_contributors_equal_commits(self):
        result = get_contributors_percentages_git(self.repo_path).output_result()
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(result['is_collaborative'], "Should be collaborative with 2 contributors")
        self.assertEqual(result['total_commits'], 2, "Should have 2 total commits")
        self.assertEqual(len(result['contributors']), 2, "Should have 2 contributors")

        for name, stats in result['contributors'].items():
            self.assertEqual(stats['commit_count'], 1, f"{name} should have 1 commit")
            self.assertEqual(stats['percentage'], '50.00%', f"{name} should have 50.00%")

    def test_output_result_structure(self):
        result = get_contributors_percentages_git(self.repo_path).output_result()
        self.assertIn('is_collaborative', result)
        self.assertIn('project_name', result)
        self.assertIn('total_commits', result)
        self.assertIn('contributors', result)

        self.assertIsInstance(result['is_collaborative'], bool)
        self.assertIsInstance(result['project_name'], str)
        self.assertIsInstance(result['total_commits'], int)
        self.assertIsInstance(result['contributors'], dict)

        for name, stats in result['contributors'].items():
            self.assertIn('commit_count', stats)
            self.assertIn('percentage', stats)
            self.assertIsInstance(stats['commit_count'], int)
            self.assertIsInstance(stats['percentage'], str)
            self.assertTrue(stats['percentage'].endswith('%'))

    def test_individual_repos(self):
        result = get_contributors_percentages_git(self.repo_path_2).output_result()
        self.assertIn('is_collaborative', result)
        self.assertFalse(result['is_collaborative'], "Should not be collaborative")
        self.assertIsInstance(result["files_change"], dict)

    def test_percentage_add_to_100(self):
        total_percentage = 0
        result = get_contributors_percentages_git(self.repo_path).output_result()
        for name, stats in result['contributors'].items():
            percentage = float(stats['percentage'].rstrip('%'))
            total_percentage += percentage
        self.assertAlmostEqual(
            total_percentage,
            100.0,
            places=1,
            msg="Contributor percentages should sum to 100%"
        )

    # ----------------- teardown -----------------

    @classmethod
    def tearDownClass(cls):
        """
        Runs ONCE after all tests.
        Clean up GitHub repos + local temp dirs.
        """
        # Delete remote GitHub repos
        if hasattr(cls, "remote_repo"):
            try:
                cls.remote_repo.delete()
                print("Deleted remote_repo")
            except Exception as e:
                print("Failed to delete remote_repo:", e)

        if hasattr(cls, "remote_repo_2"):
            try:
                cls.remote_repo_2.delete()
                print("Deleted remote_repo_2")
            except Exception as e:
                print("Failed to delete remote_repo_2:", e)

        # Close GitHub client
        if hasattr(cls, "gh"):
            try:
                cls.gh.close()
            except Exception as e:
                print("Failed to close GitHub client:", e)

        # Close repos
        if hasattr(cls, "repo"):
            try:
                cls.repo.close()
            except Exception as e:
                print("Failed to close repo:", e)

        if hasattr(cls, "repo_2"):
            try:
                cls.repo_2.close()
            except Exception as e:
                print("Failed to close repo_2:", e)

        # Remove temp directories
        for path in (
            getattr(cls, "repo_path", None),
            getattr(cls, "repo_path_2", None),
        ):
            if path and os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
                print("Deleted local directory:", path)


if __name__ == "__main__":
    unittest.main()
