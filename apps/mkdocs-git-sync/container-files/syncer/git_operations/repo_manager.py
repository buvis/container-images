import os
import re
import shutil
import logging
from typing import Optional
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class RepoManager:
    """
    Secure Git repository manager with credential masking.
    """

    def __init__(self, repo_url: str, branch: str, clone_path: str):
        self.original_url = repo_url
        self.safe_url = self._sanitize_url(repo_url)
        self.branch = branch
        self.clone_path = clone_path
        self.repo: Optional[Repo] = None

    def _sanitize_url(self, url: str) -> str:
        """Mask credentials in URLs for safe logging."""
        return re.sub(r"(https?://)([^@]+@)", r"\1***@", url)

    def clone(self) -> None:
        """Clone repository with secure logging."""
        self._prepare_directory()
        logger.info(f"Cloning repository: {self.safe_url} (branch: {self.branch})")

        try:
            self.repo = Repo.clone_from(
                self.original_url, self.clone_path, branch=self.branch
            )
        except GitCommandError as e:
            safe_error = e.stderr.replace(self.original_url, self.safe_url)
            logger.error(f"Clone failed: {safe_error.strip()}")
            raise

    def pull(self) -> None:
        """Pull latest changes safely."""
        if not self.repo:
            raise RuntimeError("Repository not initialized")

        try:
            logger.info("Pulling latest changes")
            self.repo.remotes.origin.pull()
        except GitCommandError as e:
            safe_error = e.stderr.replace(self.original_url, self.safe_url)
            logger.error(f"Pull failed: {safe_error.strip()}")
            raise

    def _prepare_directory(self) -> None:
        """Ensure clean clone directory."""
        if os.path.exists(self.clone_path):
            logger.info(f"Cleaning directory: {self.clone_path}")
            shutil.rmtree(self.clone_path)
        os.makedirs(self.clone_path, exist_ok=True)

    @property
    def head_commit(self):
        """Get current HEAD commit safely."""
        if not self.repo:
            raise RuntimeError("Repository not initialized")
        return self.repo.head.commit
