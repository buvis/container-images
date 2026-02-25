"""Git sync config CRUD + sync triggering."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

import redis
import rq

from clara.config import get_settings
from clara.exceptions import NotFoundError
from clara.git_sync.models import GitSyncConfig, GitSyncMapping
from clara.git_sync.repository import GitSyncConfigRepository, GitSyncMappingRepository
from clara.git_sync.schemas import GitSyncConfigCreate, GitSyncConfigUpdate
from clara.integrations.crypto import encrypt_credential


class GitSyncService:
    def __init__(
        self,
        config_repo: GitSyncConfigRepository,
        mapping_repo: GitSyncMappingRepository,
    ) -> None:
        self.config_repo = config_repo
        self.mapping_repo = mapping_repo

    async def get_config(self) -> GitSyncConfig:
        config = await self.config_repo.get_for_vault()
        if config is None:
            raise NotFoundError("GitSyncConfig", uuid.UUID(int=0))
        return config

    async def create_config(self, data: GitSyncConfigCreate) -> GitSyncConfig:
        fields = data.model_dump(exclude={"credential"})
        fields["credential_encrypted"] = encrypt_credential(data.credential)
        return await self.config_repo.create(**fields)

    async def update_config(self, data: GitSyncConfigUpdate) -> GitSyncConfig:
        config = await self.get_config()
        fields = data.model_dump(exclude_unset=True, exclude={"credential"})
        if data.credential is not None:
            fields["credential_encrypted"] = encrypt_credential(data.credential)
        return await self.config_repo.update(config.id, **fields)

    async def delete_config(self) -> None:
        config = await self.get_config()
        await self.config_repo.soft_delete(config.id)

    async def trigger_sync(self) -> None:
        config = await self.get_config()
        settings = get_settings()
        conn = redis.Redis.from_url(str(settings.redis_url))
        q = rq.Queue(connection=conn)
        q.enqueue("clara.jobs.git_sync.run_git_sync", str(config.id))

    async def get_status(self) -> dict[str, Any]:
        config = await self.get_config()
        count = await self.mapping_repo.count_by_config(config.id)
        return {
            "last_sync_at": config.last_sync_at,
            "last_sync_status": config.last_sync_status,
            "last_sync_error": config.last_sync_error,
            "mapping_count": count,
        }

    async def list_mappings(
        self,
    ) -> Sequence[GitSyncMapping]:
        config = await self.get_config()
        return await self.mapping_repo.list_by_config(config.id)

    async def test_connection(self) -> dict[str, Any]:
        """Clone to temp dir to verify access."""
        import tempfile

        from clara.git_sync.git_ops import GitRepo

        config = await self.get_config()
        with tempfile.TemporaryDirectory() as tmp:
            repo = GitRepo(
                work_dir=tmp,
                repo_url=config.repo_url,
                branch=config.branch,
                auth_type=config.auth_type,
                credential_encrypted=config.credential_encrypted,
            )
            try:
                repo.clone_or_open()
                files = repo.list_markdown_files(config.subfolder)
                return {"status": "ok", "markdown_files": len(files)}
            finally:
                repo.cleanup()
