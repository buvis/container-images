import os
from config_defaults import DEFAULT_BRANCH, DEFAULT_INTERVAL


class Config:
    def __init__(self):
        self.repo = os.environ["GIT_REPO"]

        if self.repo == "none":
            exit("No git repo set via GIT_REPO environment variable")

        if os.environ["GIT_CREDENTIALS"]:
            if not self.repo.startswith("https://"):
                exit("Expected repo URL to start with https://")
            else:
                self.repo = f"https://{os.environ['GIT_CREDENTIALS']}@{self.repo[8:]}"

        self.branch = os.environ["GIT_BRANCH"] or DEFAULT_BRANCH

        try:
            self.interval = int(os.environ["UPDATE_INTERVAL"])
        except ValueError:
            self.interval = DEFAULT_INTERVAL

        self._install_requirements()

    def _install_requirements(self):
        if os.path.exists("/app/config/requirements.txt"):
            os.system(
                f"python3 -m pip install --no-cache-dir -q -r /app/config/requirements.txt"
            )
