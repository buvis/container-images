from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_sync_session_factory: sessionmaker[Session] | None = None


def _get_factory() -> sessionmaker[Session]:
    global _sync_session_factory
    if _sync_session_factory is None:
        from clara.config import get_settings

        sync_url = str(get_settings().database_url)
        engine = create_engine(sync_url)
        _sync_session_factory = sessionmaker(engine)
    return _sync_session_factory


def get_sync_session() -> Session:
    factory = _get_factory()
    session: Session = factory()
    return session
