"""Git operations wrapper using GitPython."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import structlog
from git import Repo

from clara.integrations.crypto import decrypt_credential

logger = structlog.get_logger()


class GitRepo:
    """Manages a local git clone for sync."""

    def __init__(
        self,
        work_dir: str,
        repo_url: str,
        branch: str,
        auth_type: str,
        credential_encrypted: str,
    ) -> None:
        self.work_dir = Path(work_dir)
        self.repo_url = repo_url
        self.branch = branch
        self.auth_type = auth_type
        self.credential_encrypted = credential_encrypted
        self._repo: Repo | None = None
        self._ssh_key_file: str | None = None
        self._askpass_file: str | None = None

    def clone_or_open(self) -> None:
        """Clone the repo if it doesn't exist, or open + pull."""
        env = self._git_env()
        if (self.work_dir / ".git").exists():
            self._repo = Repo(str(self.work_dir))
            self._repo.git.update_environment(**env)
        else:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            url = self._auth_url()
            self._repo = Repo.clone_from(
                url, str(self.work_dir), branch=self.branch, env=env
            )

    def pull(self) -> list[str]:
        """Pull latest changes. Returns list of changed file paths."""
        assert self._repo
        before = self._repo.head.commit.hexsha
        origin = self._repo.remotes.origin
        origin.pull(self.branch)
        after = self._repo.head.commit.hexsha
        if before == after:
            return []
        diff = self._repo.git.diff("--name-only", before, after)
        return diff.strip().split("\n") if diff.strip() else []

    def list_markdown_files(self, subfolder: str = "") -> list[str]:
        """List all .md files in subfolder relative to repo root."""
        base = self.work_dir / subfolder if subfolder else self.work_dir
        if not base.exists():
            return []
        return [
            str(p.relative_to(self.work_dir))
            for p in base.rglob("*.md")
            if not p.name.startswith(".")
        ]

    def read_file(self, path: str) -> str:
        """Read a file from the repo."""
        return (self.work_dir / path).read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        """Write a file to the repo."""
        full_path = self.work_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def read_binary(self, path: str) -> bytes:
        """Read a binary file from the repo."""
        return (self.work_dir / path).read_bytes()

    def write_binary(self, path: str, data: bytes) -> None:
        """Write a binary file to the repo."""
        full_path = self.work_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

    def delete_file(self, path: str) -> None:
        """Delete a file from the repo."""
        full_path = self.work_dir / path
        if full_path.exists():
            full_path.unlink()

    def commit_and_push(self, message: str) -> bool:
        """Stage all, commit, push. Returns True if committed."""
        assert self._repo
        self._repo.git.add(A=True)
        if not self._repo.is_dirty(untracked_files=True):
            return False
        self._repo.index.commit(message)
        self._repo.remotes.origin.push(self.branch)
        return True

    def file_last_modified(self, path: str) -> str | None:
        """Get git log timestamp for a file."""
        assert self._repo
        try:
            log = self._repo.git.log("-1", "--format=%aI", "--", path)
            return log.strip() or None
        except Exception:
            return None

    def cleanup(self) -> None:
        """Clean up temp credential files."""
        for path in (self._ssh_key_file, self._askpass_file):
            if path and os.path.exists(path):
                os.unlink(path)

    def _auth_url(self) -> str:
        """Return repo URL (credentials passed via env, not URL)."""
        return self.repo_url

    def _git_env(self) -> dict[str, str]:
        """Build environment variables for git operations."""
        env: dict[str, str] = {}
        if self.auth_type == "ssh_key":
            credential = decrypt_credential(self.credential_encrypted)
            fd, path = tempfile.mkstemp(prefix="clara_ssh_", suffix=".key")
            os.write(fd, credential.encode())
            os.close(fd)
            os.chmod(path, 0o600)
            self._ssh_key_file = path
            # StrictHostKeyChecking=no: tradeoff for unattended sync.
            # Users with known_hosts can override via GIT_SSH_COMMAND.
            env["GIT_SSH_COMMAND"] = f"ssh -i {path} -o StrictHostKeyChecking=no"
        elif self.auth_type == "pat":
            credential = decrypt_credential(self.credential_encrypted)
            fd, path = tempfile.mkstemp(prefix="clara_askpass_", suffix=".sh")
            os.write(fd, f"#!/bin/sh\necho '{credential}'\n".encode())
            os.close(fd)
            os.chmod(path, 0o700)
            self._askpass_file = path
            env["GIT_ASKPASS"] = path
            env["GIT_TERMINAL_PROMPT"] = "0"
        return env
