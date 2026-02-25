"""RQ jobs for git markdown sync."""

from __future__ import annotations

import contextlib
import uuid
from datetime import UTC, datetime

import redis
import structlog
from sqlalchemy import select

from clara.config import get_settings
from clara.git_sync.git_ops import GitRepo
from clara.git_sync.models import GitSyncConfig
from clara.git_sync.sync import run_sync
from clara.jobs.sync_db import get_sync_session

logger = structlog.get_logger()

LOCK_TTL = 600  # 10 minutes


def run_git_sync(config_id: str) -> None:
    """Full sync for one git sync config."""
    settings = get_settings()
    r = redis.Redis.from_url(str(settings.redis_url))
    lock_key = f"git_sync:{config_id}"
    lock = r.lock(lock_key, timeout=LOCK_TTL)

    if not lock.acquire(blocking=False):
        logger.info("git_sync_locked", config_id=config_id)
        return

    session = get_sync_session()
    repo: GitRepo | None = None
    try:
        config = session.get(GitSyncConfig, uuid.UUID(config_id))
        if config is None or config.deleted_at is not None or not config.enabled:
            return

        config.last_sync_status = "running"
        session.flush()

        work_dir = f"{settings.git_sync_work_dir}/{config_id}"
        repo = GitRepo(
            work_dir=work_dir,
            repo_url=config.repo_url,
            branch=config.branch,
            auth_type=config.auth_type,
            credential_encrypted=config.credential_encrypted,
        )

        counts = run_sync(session, config, repo)
        session.commit()
        logger.info("git_sync_complete", config_id=config_id, counts=counts)

    except Exception as exc:
        session.rollback()
        try:
            config = session.get(GitSyncConfig, uuid.UUID(config_id))
            if config:
                config.last_sync_status = "error"
                config.last_sync_error = str(exc)[:500]
                session.commit()
        except Exception:
            session.rollback()
        logger.exception("git_sync_failed", config_id=config_id)
    finally:
        if repo:
            repo.cleanup()
        session.close()
        with contextlib.suppress(Exception):
            lock.release()


def schedule_git_syncs() -> None:
    """Check which git sync configs are due and enqueue them."""
    import rq
    from rq import Retry

    settings = get_settings()
    r = redis.Redis.from_url(str(settings.redis_url))
    q = rq.Queue(connection=r)
    session = get_sync_session()

    try:
        now = datetime.now(UTC)
        configs = (
            session.execute(
                select(GitSyncConfig).where(
                    GitSyncConfig.deleted_at.is_(None),
                    GitSyncConfig.enabled.is_(True),
                )
            )
            .scalars()
            .all()
        )
        for config in configs:
            if config.last_sync_at is None:
                q.enqueue(
                    run_git_sync,
                    str(config.id),
                    retry=Retry(max=3, interval=[10, 30, 60]),
                )
                continue
            elapsed = (now - config.last_sync_at).total_seconds() / 60
            if elapsed >= config.sync_interval_minutes:
                q.enqueue(
                    run_git_sync,
                    str(config.id),
                    retry=Retry(max=3, interval=[10, 30, 60]),
                )
    finally:
        session.close()
