import logging
from datetime import datetime
from typing import Optional

from git_operations.repo_manager import RepoManager
from mkdocs.builder import MkDocsBuilder

logger = logging.getLogger(__name__)


class Syncer:
    """
    Main synchronization service. Coordinates:
    - Repository cloning/pulling
    - Documentation building
    - Change detection
    """

    def __init__(self, config):
        self.branch = config.branch
        self.repo_url = config.repo
        self.clone_path = "/app/source_repo"
        self.prev_sha: str = ""

        # Dependencies
        self.repo_manager: Optional[RepoManager] = None
        self.mkdocs_builder = MkDocsBuilder()

        self._initialize_repository()

    def _initialize_repository(self) -> None:
        """Initial clone of the repository."""
        self.repo_manager = RepoManager(
            repo_url=self.repo_url, branch=self.branch, clone_path=self.clone_path
        )
        self.repo_manager.clone()
        self._log_commit_details(self.repo_manager.head_commit)
        self._build_docs()
        self.prev_sha = self.repo_manager.head_commit.hexsha

    def update(self) -> None:
        """Main update cycle: pull changes and rebuild if needed."""
        if not self.repo_manager:
            raise RuntimeError("Syncer not initialized properly")

        try:
            self.repo_manager.pull()
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return

        head_commit = self.repo_manager.head_commit
        new_sha = head_commit.hexsha

        if new_sha != self.prev_sha:
            self._log_commit_details(head_commit)
            self._build_docs()
            self.prev_sha = new_sha

    def _log_commit_details(self, commit) -> None:
        """Log commit details without sensitive info."""
        commit_date = datetime.fromtimestamp(commit.authored_date)
        logger.warning(
            f"New commit detected - site rebuild needed\n"
            f"  SHA: {commit.hexsha[:7]}\n"
            f"  Message: {commit.message.strip()}\n"
            f"  Date: {commit_date.isoformat()}\n"
            f"  Author: {commit.committer.name}"
        )

    def _build_docs(self) -> None:
        """Trigger documentation build."""
        try:
            self.mkdocs_builder.build()
            logger.info("Documentation built successfully")
        except Exception as e:
            logger.error(f"Documentation build failed: {str(e)}")
