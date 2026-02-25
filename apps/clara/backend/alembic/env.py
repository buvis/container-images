import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from clara.config import get_settings
from clara.base.model import Base
import clara.auth.models  # noqa: F401
import clara.contacts.models  # noqa: F401
import clara.activities.models  # noqa: F401
import clara.notes.models  # noqa: F401
import clara.reminders.models  # noqa: F401
import clara.tasks.models  # noqa: F401
import clara.journal.models  # noqa: F401
import clara.finance.models  # noqa: F401
import clara.files.models  # noqa: F401
import clara.customization.models  # noqa: F401
import clara.notifications.models  # noqa: F401
import clara.dav_sync.models  # noqa: F401
import clara.git_sync.models  # noqa: F401

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.async_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
