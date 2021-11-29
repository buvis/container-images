import git
import os
import shutil

from datetime import datetime


class Syncer:
    def __init__(self, config):
        self.branch = config.branch
        self.repo = config.repo
        self.repo_url = config.repo_url
        self.docs = "/app/source_repo"
        self.prev_sha = ""
        self._clone()

    def _clone(self):
        if not os.path.exists(self.docs):
            os.mkdir(self.docs)
        else:
            shutil.rmtree(self.docs)

        if not os.path.exists("/app/config/mkdocs.yml"):
            exit("mkdocs.yml not provided")
        print(f"Getting documentation from: {self.repo_url}")
        git.Repo.clone_from(self.repo, self.docs, branch=self.branch)
        self.local = git.Repo(self.docs)
        self.remote = self.local.remotes[0]

    def update(self):
        try:
            self.remote.pull()
        except git.GitCommandError as e:
            print(f"Repo update failed: {e.stderr}")

        headcommit = self.local.head.commit
        commit_date = datetime.fromtimestamp(headcommit.authored_date)
        new_sha = headcommit.hexsha

        if new_sha != self.prev_sha:
            print(
                f"Pulled branch: {self.branch}\n"
                f"Commit: {new_sha}\n"
                f"Commit Message: {headcommit.message}\n"
                f"Date: {commit_date}\n"
                f"Author: {headcommit.committer.name}\n"
            )
            os.system("mkdocs build -f /app/config/mkdocs.yml")

        self.prev_sha = new_sha
