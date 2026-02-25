import uuid
from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from clara.auth.models import User, Vault, VaultMembership
from clara.auth.security import hash_password
from clara.base.model import Base
from clara.jobs.reminders import _notify_vault_members
from clara.notifications.models import Notification


def _setup_db():
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    return engine


def test_notify_skips_soft_deleted_members():
    engine = _setup_db()
    with Session(engine) as session:
        user1 = User(
            email="active@test.com",
            name="Active",
            hashed_password=hash_password("x"),
        )
        user2 = User(
            email="deleted@test.com",
            name="Deleted",
            hashed_password=hash_password("x"),
        )
        vault = Vault(name="V", owner_user_id=user1.id)
        session.add_all([user1, user2, vault])
        session.flush()

        m1 = VaultMembership(user_id=user1.id, vault_id=vault.id, role="owner")
        m2 = VaultMembership(
            user_id=user2.id,
            vault_id=vault.id,
            role="member",
            deleted_at=datetime.now(UTC),
        )
        session.add_all([m1, m2])
        session.flush()

        _notify_vault_members(session, vault.id, "Test notification")

        notifications = session.execute(select(Notification)).scalars().all()
        assert len(notifications) == 1
        assert notifications[0].user_id == user1.id
