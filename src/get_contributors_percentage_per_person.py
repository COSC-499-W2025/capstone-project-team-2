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
        self.local_contributors = None
        self.project_info = None
        load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        self.final_url = None
        self.repo_name=None
        self.total_commits=0
        self.file_path=file_path
        self.author_count=Counter()
        self.state_1=None
        self.state_2=None



    def get_repo_link(self):
        try:
            local_repo = Repo(self.file_path)
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
        Here I am I

        """
        auth = Auth.Token(self.token)
        g = Github(auth=auth)
        """
        rate_limit = g.get_rate_limit()
        core = rate_limit.rate

        print(f"Rate Limit: {core.limit}")
        print(f"Remaining: {core.remaining}")
        print(f"Resets at: {core.reset}")
        """



        if self.final_url is not None:
            repo = g.get_repo(self.final_url)
            #author_count = Counter()
            #remote_repo_contributors=repo.get_contributors().totalCount

            #if self.local_contributors != remote_repo_contributors:
                #contributors = self.local_contributors

            #else:
            #    contributors=remote_repo_contributors




            #self.project_Collab = (True if contributors > 1 else False)
            self.repo_name=repo.full_name
            seen_shas=set()


            for pos,branch in enumerate(repo.get_branches()):
                branch_name = branch.name
                #print(f"Collecting data on {pos+1} {branch_name} ")
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

                    self.author_count[author_login] += 1
                    self.total_commits += 1


            g.close()
            return "Data successfully collected"

        return "Data unsuccessfully collected"



    def output_result(self):
        self.state_1=self.get_repo_link()
        self.state_2=self.get_repo_info()


        if self.state_1 != "Not a git repository" and self.state_2 != "Data unsuccessfully collected":

            self.project_info= {"is_collaborative": False, "project_name": self.repo_name,
                            "total_commits": self.total_commits, "contributors": {}}

            for login,count in self.author_count.most_common():
                pct=(count/self.total_commits)*100 if self.total_commits>0 else 0
                self.project_info["contributors"][login]={
                    "commit_count":count,
                    "percentage":f"{pct:.2f}%",
                }

            num_of_contributors=len(self.project_info.get("contributors").keys())
            if num_of_contributors>1:
                self.project_info["is_collaborative"]=True


            return self.project_info
        return "Data unsuccessfully collected"


#test=get_contributors_percentages_git(r"D:\UBCO\COSC_305_project-management")
#print(test.output_result())
#print(test.state_1,test.state_2)






