from pathlib import Path
import shutil
from src.get_contributors_percentage_per_person import get_contributors_percentages_git
import unittest
import tempfile
from git import Repo, Actor
from github import Github,Auth
import os
from dotenv import load_dotenv
import uuid
import gc



class TestIndividualContributionDetection_percentage_git(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.repo_path = tempfile.mkdtemp()
        self.repo=Repo.init(self.repo_path)

        file_path=os.path.join(self.repo_path,"file.txt")
        with open(file_path,"w") as f:
            f.write("Hello 1")

        self.repo.git.add(A=True)
        self.repo.index.commit("Commit A", author=Actor("Alice", "alice@example.com"))

        with open(file_path, "a") as f:
            f.write("Hello 2")

        self.repo.git.add(A=True)
        self.repo.index.commit("Commit B", author=Actor("Bob", "bob@example.com"))

        auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
        self.gh = Github(auth=auth)
        user=self.gh.get_user()

        repo_name = f"test-repo-temp-{uuid.uuid4().hex[:8]}"
        self.remote_repo=user.create_repo(
            name=repo_name,
            private=False,
        )

        self.repo.create_remote("origin", self.remote_repo.clone_url.replace(
            "https://",
            f"https://{os.getenv('GITHUB_TOKEN')}@"
        ))

        self.repo.git.push("--set-upstream","origin","master")

    def test_two_contributors_equal_commits(self):
        result=get_contributors_percentages_git(self.repo_path).output_result()
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(result['is_collaborative'], "Should be collaborative with 2 contributors")
        self.assertEqual(result['total_commits'], 2, "Should have 2 total commits")
        self.assertEqual(len(result['contributors']), 2, "Should have 2 contributors")

        for name, stats in result['contributors'].items():
            self.assertEqual(stats['commit_count'], 1, f"{name} should have 1 commit")
            self.assertEqual(stats['percentage'], '50.00%', f"{name} should have 50.00%")


    def test_output_result_structure(self):
        result=get_contributors_percentages_git(self.repo_path).output_result()
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


    def test_percentage_add_to_100(self):
        total_percentage=0
        result=get_contributors_percentages_git(self.repo_path).output_result()
        for name, stats in result['contributors'].items():
            percentage=float(stats['percentage'].rstrip('%'))
            total_percentage+=percentage
        self.assertAlmostEqual(total_percentage, 100.0, places=1,msg="Contributor percentages should sum to 100%")






    def tearDown(self):

        if hasattr(self,"repo"):
            self.repo.close()
            del self.repo




        if hasattr(self,"remote_repo"):
            self.remote_repo.delete()

        if hasattr(self,"gh"):
            self.gh.close()

        if hasattr(self, 'repo_path') and os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)
            print(f"Cleaned up local repo: {self.repo_path}")


if __name__ == "__main__":
    unittest.main()