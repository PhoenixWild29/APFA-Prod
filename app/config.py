from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # MinIO / Object Storage
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    
    # AI/ML Models
    llm_model_name: str = "meta-llama/Llama-3-8b-hf"
    embedder_model: str = "all-MiniLM-L6-v2"
    delta_table_path: str = "s3a://customer-data-lakehouse/customers"
    
    # Logging
    log_level: str = "INFO"
    debug: bool = False
    
    # API Security
    api_key: str
    
    # JWT Authentication
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CSRF Protection
    csrf_secret: str = "your-csrf-secret-change-in-production"
    csrf_token_expire_hours: int = 24
    
    # Cookie Configuration
    cookie_domain: str = "localhost"
    cookie_secure: bool = False  # Set to True in production with HTTPS
    cookie_samesite: str = "strict"  # strict, lax, or none
    
    # AWS Cognito (for future migration)
    cognito_user_pool_id: str = "us-east-1_xxxxxxx"  # Placeholder
    cognito_client_id: str = "xxxxxxxxxxxxxxxxxxxxxxxxxx"  # Placeholder
    cognito_domain: str = "https://your-cognito-domain.auth.us-east-1.amazoncognito.com"  # Placeholder
    
    # Email Configuration (for verification emails)
    email_from: str = "noreply@apfa.io"
    email_verification_url: str = "http://localhost:3000/verify"
    
    # Document Upload Configuration
    s3_bucket_name: str = "apfa-documents"
    allowed_document_types: List[str] = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    max_file_size_mb: int = 50
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    
    class Config:
        env_file = ".env"

settings = Settings()