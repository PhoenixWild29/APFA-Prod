"""SQLAlchemy database engine, session factory, and declarative Base.

This module wires up the connection to PostgreSQL. The connection string comes
from settings.database_url which is populated from the DATABASE_URL environment
variable (already set in docker-compose.yml).

Usage:
    from app.database import get_db, Base
    from app.orm_models import User

    @app.get("/users")
    async def list_users(db: Session = Depends(get_db)):
        return db.query(User).all()
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# Engine: connection pool to PostgreSQL. pool_pre_ping=True prevents stale
# connections after DB restart or network blip.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,  # recycle connections after 1 hour
)

# SessionLocal: per-request session factory. Each HTTP request gets its own
# session via the get_db() dependency, and the session is closed after the
# request completes.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: declarative base class for ORM models. All ORM models inherit from this.
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and ensures cleanup.

    Usage in endpoints:
        async def my_endpoint(db: Session = Depends(get_db)):
            return db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
