FROM python:3.11-slim as base

# Security: Create non-root user with home directory (-m) for HuggingFace
# model cache. Without -m, useradd -r skips home dir creation and
# sentence-transformers crashes with PermissionError on /home/apfa.
RUN groupadd -r apfa && useradd -r -g apfa -m apfa

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# APFA-013.5: WORKDIR is the repo root, not app/ — so `from app.X import Y`
# resolves correctly (app/ is a subdirectory with __init__.py).
WORKDIR /opt/apfa

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN chown -R apfa:apfa /usr/local/lib/python3.11 /usr/local/bin

# Copy application code and entrypoint
COPY app/ ./app/
COPY entrypoint.sh ./entrypoint.sh

# Change ownership to non-root user
RUN chown -R apfa:apfa /opt/apfa
USER apfa

# Health check
# start-period=180s covers Alembic migrations + ML model pre-loading on
# cold start. retries=5 gives another 2.5min grace after the start period.
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Entrypoint runs Alembic migrations before starting uvicorn.
# Migrations run once, synchronously, outside the async event loop.
# If migration fails, container exits before uvicorn starts.
CMD ["/opt/apfa/entrypoint.sh"]
