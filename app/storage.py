"""Central storage configuration for delta-rs / MinIO S3-compatible access."""


def get_delta_storage_options() -> dict:
    """Return storage_options dict for delta-rs to connect to MinIO.

    Used by load_rag_index() and the RAG seed script to ensure both read
    and write paths use identical authentication and endpoint config.
    """
    from app.config import settings

    endpoint = settings.minio_endpoint
    if not endpoint.startswith("http"):
        endpoint = f"http://{endpoint}"

    return {
        "AWS_ENDPOINT_URL": endpoint,
        "AWS_ACCESS_KEY_ID": settings.minio_access_key,
        "AWS_SECRET_ACCESS_KEY": settings.minio_secret_key,
        "AWS_REGION": settings.aws_region,
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
        "AWS_ALLOW_HTTP": "true",
    }
