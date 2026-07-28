"""
Shared SQLAlchemy engine/session factory. Each microservice owns its own
database (see architecture doc: database-per-service), so each service
instantiates its own engine using its own DATABASE_URL, but reuses this helper.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)


def make_session_factory(engine) -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_dependency(session_factory: sessionmaker):
    """Returns a FastAPI dependency that yields a DB session per request."""

    def _get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return _get_db
