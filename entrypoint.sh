#!/bin/sh
set -e

# Remove stale sentinel from previous container lifecycle
rm -f /tmp/migrations_done

echo "Running database migrations..."
python -m alembic -c app/alembic.ini upgrade head
echo "Migrations complete."

# Signal to Docker healthcheck that migrations finished successfully.
# The healthcheck waits for this file before probing /health, preventing
# wasted retries while Alembic is still running.
touch /tmp/migrations_done

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
