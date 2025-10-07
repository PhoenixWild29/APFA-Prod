from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    aws_region: str = "us-east-1"
    llm_model_name: str = "meta-llama/Llama-3-8b-hf"
    embedder_model: str = "all-MiniLM-L6-v2"
    delta_table_path: str = "s3a://customer-data-lakehouse/customers"
    log_level: str = "INFO"
    api_key: str
    debug: bool = False
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()