"""DAV sync account CRUD + sync triggering."""

from __future__ import annotations

import uuid
from typing import Any

import redis
import rq

from clara.config import get_settings
from clara.dav_sync.client import DavClient
from clara.dav_sync.models import DavSyncAccount
from clara.dav_sync.repository import DavSyncAccountRepository, DavSyncMappingRepository
from clara.dav_sync.schemas import DavSyncAccountCreate, DavSyncAccountUpdate
from clara.exceptions import NotFoundError
from clara.integrations.crypto import decrypt_credential, encrypt_credential


class DavSyncService:
    def __init__(
        self,
        account_repo: DavSyncAccountRepository,
        mapping_repo: DavSyncMappingRepository,
    ) -> None:
        self.account_repo = account_repo
        self.mapping_repo = mapping_repo

    async def list_accounts(self) -> list[DavSyncAccount]:
        items, _ = await self.account_repo.list(offset=0, limit=1000)
        return list(items)

    async def get_account(self, account_id: uuid.UUID) -> DavSyncAccount:
        account = await self.account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError("DavSyncAccount", account_id)
        return account

    async def create_account(self, data: DavSyncAccountCreate) -> DavSyncAccount:
        fields = data.model_dump(exclude={"password"})
        fields["encrypted_password"] = encrypt_credential(data.password)
        return await self.account_repo.create(**fields)

    async def update_account(
        self, account_id: uuid.UUID, data: DavSyncAccountUpdate
    ) -> DavSyncAccount:
        fields = data.model_dump(exclude_unset=True, exclude={"password"})
        if data.password is not None:
            fields["encrypted_password"] = encrypt_credential(data.password)
        return await self.account_repo.update(account_id, **fields)

    async def delete_account(self, account_id: uuid.UUID) -> None:
        await self.account_repo.soft_delete(account_id)

    async def test_connection(self, account_id: uuid.UUID) -> dict[str, str | None]:
        account = await self.get_account(account_id)
        password = decrypt_credential(account.encrypted_password)
        client = DavClient(account.server_url, account.username, password)
        return client.test_connection()

    async def trigger_sync(self, account_id: uuid.UUID) -> None:
        """Enqueue sync job."""
        await self.get_account(account_id)  # validate exists
        settings = get_settings()
        conn = redis.Redis.from_url(str(settings.redis_url))
        q = rq.Queue(connection=conn)
        q.enqueue("clara.jobs.dav_sync.sync_dav_account", str(account_id))

    async def get_status(self, account_id: uuid.UUID) -> dict[str, Any]:
        account = await self.get_account(account_id)
        counts = await self.mapping_repo.count_by_account(account_id)
        return {
            "last_synced_at": account.last_synced_at,
            "last_sync_status": account.last_sync_status,
            "last_sync_error": account.last_sync_error,
            "mapping_counts": counts,
        }
