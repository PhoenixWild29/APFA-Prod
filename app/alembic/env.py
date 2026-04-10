"""Alembic migration environment for APFA.

Key differences from the default alembic template:
- Reads the connection URL from settings.database_url (not alembic.ini)
- Imports Base metadata from app.database + app.orm_models so autogenerate works
- Supports both offline (SQL script) and online (live DB) modes
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the app package is importable when alembic runs from the repo root
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402
from app.database import Base  # noqa: E402

# Import all ORM models so Alembic's autogenerate sees them
from app.orm_models import User  # noqa: E402,F401

# Alembic Config object, provides access to alembic.ini values
config = context.config

# Override sqlalchemy.url with the runtime value from app config
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL without connecting to a DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connect to the DB and apply."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
