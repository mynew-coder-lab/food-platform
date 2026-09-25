from sqlalchemy import create_engine, MetaData

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
metadata = MetaData()


def get_connection():
    """FastAPI dependency that yields a Core connection wrapped in a
    transaction: commits on success, rolls back if the request raises."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            yield conn
            trans.commit()
        except Exception:
            trans.rollback()
            raise
