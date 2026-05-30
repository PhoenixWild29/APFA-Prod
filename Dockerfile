FROM python:3.11-slim

# Security: Create non-root user with home directory (-m).
# fastembed caches ONNX models; we override the cache path to
# /opt/apfa/models but keep -m for tools that expect a writable home.
RUN groupadd -r apfa && useradd -r -g apfa -m apfa

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/apfa

# Install Python dependencies (--no-cache-dir saves ~100MB of pip cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN chown -R apfa:apfa /usr/local/lib/python3.11 /usr/local/bin

# Bake fastembed ONNX models into the image layer (~330MB).
# Eliminates model download on every cold start. Model names must
# match app/config.py embedder_model and reranker_model defaults.
# TextCrossEncoder is optional (reranker_enabled defaults to False).
RUN python -c "\
from fastembed import TextEmbedding; \
TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='/opt/apfa/models'); \
print('Embedder model baked.'); \
try: \
    from fastembed import TextCrossEncoder; \
    TextCrossEncoder(model_name='BAAI/bge-reranker-base', cache_dir='/opt/apfa/models'); \
    print('Reranker model baked.'); \
except ImportError: \
    print('TextCrossEncoder not available — reranker will download at runtime if enabled.'); \
print('Model bake complete.')"

# Copy application code and entrypoint
COPY app/ ./app/
COPY entrypoint.sh ./entrypoint.sh

# Change ownership to non-root user (includes baked model cache)
RUN chown -R apfa:apfa /opt/apfa
USER apfa

# Tell fastembed where to find pre-cached models (backstop for any
# instantiation site that forgets the explicit cache_dir parameter)
ENV FASTEMBED_CACHE_PATH=/opt/apfa/models

# Models are pre-cached — startup cost is Alembic migrations + FAISS
# index load. 90s start-period covers steady-state deploys.
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Entrypoint runs Alembic migrations before starting uvicorn.
CMD ["/opt/apfa/entrypoint.sh"]
