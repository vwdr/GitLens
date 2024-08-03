class GitRepository:
    def __init__(self, name, url):
        self.repo_id = None

        self.name = name
        self.url = url
        self.description = ""
        self.languages = []
        self.files = {}
        self.commits = []
        self.last_modified = None

        self.local_path = None

        # query scores
        self.query_relevances = {}


class GitFile:
    def __init__(self, path, num_commits):
        self.path = path  # includes the name
        self.num_commits = num_commits
        self.score = 0
        self.relevant_code = []

        self.repo = None

    def __repr__(self):
        repo_path = self.repo.local_path
        return f"{repo_path}/{self.path}: {self.num_commits} commits\n"


class GitCommit:
    def __init__(self, sha, message, date):
        self.sha = sha
        self.message = message
        self.date = date
        self.files = []

    def __repr__(self):
        return f"Commit: {self.sha[:4]} - {self.message} - {self.date}"
