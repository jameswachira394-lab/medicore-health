from shared_common.database import Base, make_engine, make_session_factory, get_db_dependency

from app.core.config import settings

engine = make_engine(settings.DATABASE_URL)
SessionLocal = make_session_factory(engine)
get_db = get_db_dependency(SessionLocal)
