from pathlib import Path

from github import Github, Auth
from git import Actor, Repo, InvalidGitRepositoryError
from collections import Counter, defaultdict
import os
from dotenv import load_dotenv


class get_contributors_percentages_git:

    """
    This is a class that Analyze a git repository contributions using GitHub API,
    where it extracts contributor stats from a local git repository through connecting to
    GitHub API to fetch commit data and calculate each  contributor's percentage of total commits.


    Attributes:
        file_path (str): The path of the local git repository.
        Project_info (dict or None): Final analysis results containing collaboration
            status, project name, total commits, and contributor statistics.
        final_url (str or None): GitHub repository URL in format 'owner/repo'.
        state_1 (str or None): Status message from repository link extraction.
        state_2 (str or None): Status message from repository info collection.

    """


    def __init__(self,file_path):

        """
        Args:
            file_path (str): The path of the local git repository.

        Sets up:
            - loads GitHub API credentials from dotenv(.env)
            - Initializes all instance variables to default values
            - Prepares Counter for tracking author commits

        """
        self.collab_project = False
        self.local_contributors = None
        self.project_info = None
        load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. Please add it to your .env file."
            )
        self.final_url = None
        self.repo_name=None
        self.total_commits=0
        self.file_path=file_path
        self.author_count=Counter()
        self.state_1=None
        self.state_2=None
        self.contributors_set=set()
        self.auth = Auth.Token(self.token)
        self.g= Github(auth=self.auth)

        self._remote_repo = None


    def _ensure_repo(self):
        if self.final_url is None:
            self.get_repo_link()

        if self.final_url is None:
            raise RuntimeError(
                "Could not determine remote GitHub repository URL from local repo."
            )

        if self._remote_repo is None:
            self._remote_repo = self.g.get_repo(self.final_url)
        return self._remote_repo






    def get_repo_link(self):
        try:
            local_repo = Repo(self.file_path) # Here I am using the gitpython library to initialize the repo
            counter=Counter()
            # Method 1: Get the origin URL (most common)
            origin_url = (str(local_repo.remotes.origin.url).split("/"))
            repo_name = origin_url[-1].split(".")[0]
            repo_owner = origin_url[-2]
            self.final_url = f"{repo_owner}/{repo_name}"
            for commit in local_repo.iter_commits():
                author_name= commit.author.name
                counter[author_name] += 1

            self.local_contributors = len(counter)
            local_repo.close()

        except InvalidGitRepositoryError:
            self.final_url = None
            return "Not a git repository"
        return "Successfully  created repo url"






    def get_repo_info(self):
        """
        Here we are connecting to the GitHub API
        to retrieve metadata about a GitHub repository,
        which includes the number of commits per author across
        all branches in the repository.

        This method connects to the GitHub API  using the stored
        authentication token (`self.auth`), retrieving the repository infromation
        from self.final_url, and iterates through each branch and commits to build up
        contributor statistics




        """

        """
        rate_limit = g.get_rate_limit()
        core = rate_limit.rate

        print(f"Rate Limit: {core.limit}")
        print(f"Remaining: {core.remaining}")
        print(f"Resets at: {core.reset}")
        """



        if self.final_url is not None:
            #repo = self.g.get_repo(self.final_url)
            repo=self._ensure_repo()
            #Here I am Initialing the repo to be used by the GitHub API

            self.repo_name=repo.full_name #Here we are retrieving the full name of the repo
            seen_shas=set()

            #here we start collecting data about the GitHub Repository
            for pos,branch in enumerate(repo.get_branches()): #Getting the remote branches names
                branch_name = branch.name
                print(f"Collecting data on {pos+1} {branch_name} ")
                for commit in repo.get_commits(sha=branch_name):
                    sha=commit.sha
                    if sha in seen_shas:
                        continue
                    seen_shas.add(sha)
                    author = commit.author
                    if author is None:
                        author_login = "Unknown"
                    else:
                        author_login = author.login or "Unknown"

                    self.author_count[author_login] += 1 #here we add the user logins information to the collection Object
                    self.total_commits += 1 #Here we add to the total commits done throughout the project/Repo


            return "Data successfully collected"

        return "Data unsuccessfully collected"


    def get_files_by_author(self):

        """
        Retrieve per-author file modification statistics from a GitHub repository.


        """

        total_changes=0
        #contributors = set()

        Remote_repo=self._ensure_repo()
        self.contributors_set={c.login for c in Remote_repo.get_contributors()}
        author_stats=defaultdict(
            lambda: defaultdict(lambda:{
                "additions":0,
                "deletions":0,
                "changes":0,
            }),
        )


        seen_shas=set()
        for branch in Remote_repo.get_branches():
            branch_name = branch.name
            #print(branch_name)
            for author in self.contributors_set:
                commits = Remote_repo.get_commits(author=author,sha=branch_name)
                for commit in commits:
                    if commit.sha in seen_shas:
                        continue
                    seen_shas.add(commit.sha)

                    detailed_info=Remote_repo.get_commit(commit.sha)
                    for file in detailed_info.files:
                        if not file.patch:
                            continue

                        suffix=Path(file.filename).suffix.lower()



                        stats=author_stats[author][file.filename]
                        stats.setdefault("fileType",suffix)
                        stats["additions"] += file.additions or 0
                        stats["deletions"] += file.deletions or 0
                        stats["changes"] += file.changes or 0

            final_dict = {}
            for author, files in author_stats.items():
                files_dict = dict(files)
                total_changes = sum(s["changes"] for s in files_dict.values())

                final_dict[author] = {
                    "files": files_dict,
                    "total_changes": total_changes,
                }

            return final_dict








    def output_result(self):
        """
        Here we are talking the metadata we received and then output in dictionary format to be used
        in other parts of the program
        :return:
        """
        self.state_1=self.get_repo_link()
        self.state_2=self.get_repo_info()
        files=self.get_files_by_author()


        if self.state_1 != "Not a git repository" and self.state_2 != "Data unsuccessfully collected":

            self.project_info= {"is_collaborative": False, "project_name": self.repo_name,
                            "total_commits": self.total_commits, "contributors": {}}

            for login,count in self.author_count.most_common():
                pct=(count/self.total_commits)*100 if self.total_commits>0 else 0 #Here I am calculating the percentage contribution for each person
                self.project_info["contributors"][login]={
                    "commit_count":count,
                    "percentage":f"{pct:.2f}%",
                } #Here we are getting the percentage of the work done by each person and storting this in the dictionary per person

            num_of_contributors=len(self.project_info.get("contributors").keys()) #Here I am seeing if project is either a collabartive here
            if num_of_contributors>1:# if its greater one, I set the dictionary flag to True
                self.collab_project=True
                self.project_info["is_collaborative"]=True


            if not self.collab_project: #Here I am seeing if the project is collaborative if it's not than I add the files change dictionary to the project_info
                self.project_info["files_change"]=files

            self.g.close()
            return self.project_info
        return "Data unsuccessfully collected"

