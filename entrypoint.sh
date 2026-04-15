#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic -c app/alembic.ini upgrade head
echo "Migrations complete."

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
