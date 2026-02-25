from datetime import UTC, datetime, timedelta
from importlib import import_module

from sqlalchemy import delete

from clara.auth.models import PersonalAccessToken
from clara.base.model import Base
from clara.jobs.sync_db import get_sync_session

_MODEL_MODULES = (
    "clara.activities.models",
    "clara.auth.models",
    "clara.contacts.models",
    "clara.customization.models",
    "clara.files.models",
    "clara.finance.models",
    "clara.journal.models",
    "clara.notes.models",
    "clara.reminders.models",
    "clara.tasks.models",
)


def _load_models() -> None:
    for module_name in _MODEL_MODULES:
        import_module(module_name)


def cleanup_expired_tokens() -> None:
    session = get_sync_session()
    try:
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=90)
        session.execute(
            delete(PersonalAccessToken).where(
                PersonalAccessToken.expires_at.is_not(None),
                PersonalAccessToken.expires_at < now,
            )
        )
        _load_models()
        for table in reversed(Base.metadata.sorted_tables):
            if "vault_id" not in table.c or "deleted_at" not in table.c:
                continue
            session.execute(
                delete(table).where(
                    table.c.deleted_at.is_not(None),
                    table.c.deleted_at < cutoff,
                )
            )
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    cleanup_expired_tokens()
