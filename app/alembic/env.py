"""Alembic migration environment for APFA.

Key differences from the default alembic template:
- Reads the connection URL from settings.database_url (not alembic.ini)
- Imports Base metadata from app.database + app.orm_models so autogenerate works
- Supports both offline (SQL script) and online (live DB) modes
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# APFA-013.5: sys.path hack removed — alembic.ini's prepend_sys_path now
# adds the repo root to sys.path, making `from app.X import Y` work cleanly.
from app.config import settings
from app.database import Base

# Import all ORM models so Alembic's autogenerate sees them
from app.orm_models import User  # noqa: F401

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
