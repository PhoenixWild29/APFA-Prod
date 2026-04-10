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

# Engine: connection pool to PostgreSQL.
#
# Pool configuration notes:
# - pool_size=10: base connection pool size (default was 5)
# - max_overflow=20: additional connections beyond pool_size under load
# - pool_recycle=3600: recycle connections hourly to avoid DB idle timeouts
# - pool_pre_ping=True: lightweight SELECT 1 before each checkout to detect
#   dead connections (prevents stale connection errors after DB restart
#   or network blips)
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# SessionLocal: per-request session factory. Each HTTP request gets its own
# session via the get_db() dependency, and the session is closed after the
# request completes.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: declarative base class for ORM models. All ORM models inherit from this.
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and ensures cleanup.

    On success: session is closed in finally.
    On exception: session is rolled back before being closed — prevents
    half-applied transactions from leaking into the next request.

    Usage in endpoints:
        async def my_endpoint(db: Session = Depends(get_db)):
            return db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
