from github import Github, Auth
from git import Actor, Repo, InvalidGitRepositoryError
from collections import Counter
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
        self.project_info = None
        load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        self.final_url = None
        self.project_Collab=False
        self.repo_name=None
        self.total_commits=0
        self.file_path=file_path
        self.author_count=Counter()
        self.state_1=None
        self.state_2=None



    def get_repo_link(self):
        try:
            repo = Repo(self.file_path)

            # Method 1: Get the origin URL (most common)
            origin_url = (str(repo.remotes.origin.url).split("/"))
            repo_name = origin_url[-1].split(".")[0]
            repo_owner = origin_url[-2]
            self.final_url = f"{repo_owner}/{repo_name}"
            repo.close()

        except InvalidGitRepositoryError:
            self.final_url = None
            return "Not a git repository"
        return "Successfully created url"



    def get_repo_info(self):
        """
        Here I am I

        """
        auth = Auth.Token(self.token)
        g = Github(auth=auth)

        if self.final_url is not None:
            repo = g.get_repo(self.final_url)
            #author_count = Counter()
            contributors = repo.get_contributors().totalCount

            self.project_Collab = (True if contributors > 1 else False)
            self.repo_name=repo.full_name


            for commit in repo.get_commits():
                author = commit.author
                if author is None:
                    author_login = "Unknown"
                else:
                    author_login = author.login or "Unknown"

                self.author_count[author_login]+=1
                self.total_commits=sum(self.author_count.values())

                g.close()
                return "Data successfully collected"
        return "Data unsuccessfully collected"

    def output_result(self):
        self.state_1=self.get_repo_link()
        self.state_2=self.get_repo_info()


        if self.state_1 != "Not a git repository" and self.state_2 != "Data unsuccessfully collected":

            self.project_info= {"is_collaborative": self.project_Collab, "project_name": self.repo_name,
                            "total_commits": self.total_commits, "contributors": {}}

            for login,count in self.author_count.most_common():
                pct=(count/self.total_commits)*100 if self.total_commits>0 else 0
                self.project_info["contributors"][login]={
                    "commit_count":count,
                    "percentage":f"{pct:.2f}%",
                }

            return self.project_info
        return None


test=get_contributors_percentages_git(r"D:\UBCO\New folder")




