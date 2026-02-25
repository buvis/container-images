"""RQ jobs for DAV sync."""

from __future__ import annotations

import contextlib
import uuid
from datetime import UTC, datetime

import redis
import structlog
from sqlalchemy import select

from clara.config import get_settings
from clara.dav_sync.client import DavClient
from clara.dav_sync.models import DavSyncAccount
from clara.dav_sync.sync_engine import sync_entity_type
from clara.integrations.crypto import decrypt_credential
from clara.jobs.sync_db import get_sync_session

logger = structlog.get_logger()

LOCK_TTL = 600  # 10 minutes


def sync_dav_account(account_id: str) -> None:
    """Sync all entity types for one DAV account."""
    settings = get_settings()
    r = redis.Redis.from_url(str(settings.redis_url))
    lock_key = f"dav_sync:{account_id}"
    lock = r.lock(lock_key, timeout=LOCK_TTL)

    if not lock.acquire(blocking=False):
        logger.info("dav_sync_locked", account_id=account_id)
        return

    session = get_sync_session()
    try:
        account = session.get(DavSyncAccount, uuid.UUID(account_id))
        if account is None or account.deleted_at is not None:
            return

        account.last_sync_status = "running"
        session.flush()

        password = decrypt_credential(account.encrypted_password)
        client = DavClient(account.server_url, account.username, password)

        all_counts: dict[str, int] = {}
        had_errors = False
        entity_types = ("contact", "activity", "task", "reminder")
        failed_count = 0
        for entity_type in entity_types:
            try:
                counts = sync_entity_type(session, client, account, entity_type)
                for k, v in counts.items():
                    all_counts[k] = all_counts.get(k, 0) + v
            except Exception:
                had_errors = True
                failed_count += 1
                logger.exception(
                    "dav_sync_entity_failed",
                    entity_type=entity_type,
                    account_id=account_id,
                )

        account.last_synced_at = datetime.now(UTC)
        if failed_count == len(entity_types):
            account.last_sync_status = "error"
        elif had_errors:
            account.last_sync_status = "partial"
        else:
            account.last_sync_status = "ok"
        account.last_sync_error = None
        session.commit()
        logger.info("dav_sync_complete", account_id=account_id, counts=all_counts)

    except Exception as exc:
        session.rollback()
        try:
            account = session.get(DavSyncAccount, uuid.UUID(account_id))
            if account:
                account.last_sync_status = "error"
                account.last_sync_error = str(exc)[:500]
                session.commit()
        except Exception:
            session.rollback()
        logger.exception("dav_sync_failed", account_id=account_id)
    finally:
        session.close()
        with contextlib.suppress(Exception):
            lock.release()


def schedule_dav_syncs() -> None:
    """Check which DAV accounts are due for sync and enqueue them."""
    import rq
    from rq import Retry

    settings = get_settings()
    r = redis.Redis.from_url(str(settings.redis_url))
    q = rq.Queue(connection=r)
    session = get_sync_session()

    try:
        now = datetime.now(UTC)
        accounts = (
            session.execute(
                select(DavSyncAccount).where(DavSyncAccount.deleted_at.is_(None))
            )
            .scalars()
            .all()
        )
        for account in accounts:
            if account.last_synced_at is None:
                q.enqueue(
                    sync_dav_account,
                    str(account.id),
                    retry=Retry(max=3, interval=[10, 30, 60]),
                )
                continue
            elapsed = (now - account.last_synced_at).total_seconds() / 60
            if elapsed >= account.sync_interval_minutes:
                q.enqueue(
                    sync_dav_account,
                    str(account.id),
                    retry=Retry(max=3, interval=[10, 30, 60]),
                )
    finally:
        session.close()
