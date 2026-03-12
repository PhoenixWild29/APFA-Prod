"""
Data models for APFA application

This package contains Pydantic data models for:
- Authentication and login events
- User profiles and sessions
- Security monitoring and alerts
- User registration and verification
"""

from app.models.access_control import AccessDecision, AccessRequest
from app.models.advice_response import BiasDetectionResults, OptimizedAdviceResponse
from app.models.alert_models import AlertEvent, AlertRule
from app.models.auth_events import AuthenticationEvent, WebSocketAuthMessage
from app.models.cache_performance import CacheEvent, CachePerformanceMetrics
from app.models.celery_tasks import (
    EmbeddingBatchTask,
    IndexBuildTask,
    TaskStatus,
    TaskStatusEnum,
)
from app.models.document_batch import DocumentBatch, ProcessingOptions
from app.models.document_management import BatchProgress, Document, DocumentBatch
from app.models.document_processing import (
    DocumentProcessingEvent,
    WebSocketDocumentMessage,
)
from app.models.document_upload import DocumentMetadata, UploadState, UploadStatus
from app.models.embedding_models import EmbeddingBatch, VectorEmbedding
from app.models.faiss_models import FAISSIndexMetadata, IndexPerformanceMetrics
from app.models.login_events import LoginEvent, WebSocketLoginMessage
from app.models.monitoring_events import SystemMetricsEvent, WebSocketMetricsMessage
from app.models.performance_snapshot import PerformanceSnapshot, SystemResourceMetrics
from app.models.performance_tracking import (
    AgentExecutionStep,
    CachedAdviceResponse,
    CacheInteraction,
    CacheMetadata,
    ResponseMetrics,
)
from app.models.rbac import Permission, Role, UserRoleAssignment
from app.models.rbac_events import RBACEvent, WebSocketRBACMessage
from app.models.token_models import (
    TokenEvent,
    TokenMetadata,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenRevocationRequest,
    TokenValidationResult,
    WebSocketTokenMessage,
)
from app.models.user_login import LoginResponse, UserLoginRequest
from app.models.user_profile import SessionMetadata, UserProfile
from app.models.user_registration import (
    RegistrationEvent,
    RegistrationResponse,
    UserRegistrationRequest,
    WebSocketRegistrationMessage,
)

__all__ = [
    "LoginEvent",
    "WebSocketLoginMessage",
    "AuthenticationEvent",
    "WebSocketAuthMessage",
    "UserProfile",
    "SessionMetadata",
    "UserRegistrationRequest",
    "RegistrationResponse",
    "RegistrationEvent",
    "WebSocketRegistrationMessage",
    "UserLoginRequest",
    "LoginResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "TokenRevocationRequest",
    "TokenEvent",
    "WebSocketTokenMessage",
    "TokenMetadata",
    "TokenValidationResult",
    "DocumentProcessingEvent",
    "WebSocketDocumentMessage",
    "Document",
    "BatchProgress",
    "DocumentBatch",
    "IndexPerformanceMetrics",
    "FAISSIndexMetadata",
    "DocumentMetadata",
    "UploadStatus",
    "UploadState",
    "Role",
    "Permission",
    "UserRoleAssignment",
    "RBACEvent",
    "WebSocketRBACMessage",
    "AccessRequest",
    "AccessDecision",
    "EmbeddingBatchTask",
    "IndexBuildTask",
    "TaskStatus",
    "TaskStatusEnum",
    "DocumentBatch",
    "ProcessingOptions",
    "EmbeddingBatch",
    "VectorEmbedding",
    "CachedAdviceResponse",
    "ResponseMetrics",
    "CacheMetadata",
    "CacheInteraction",
    "AgentExecutionStep",
    "OptimizedAdviceResponse",
    "BiasDetectionResults",
    "SystemMetricsEvent",
    "WebSocketMetricsMessage",
    "PerformanceSnapshot",
    "SystemResourceMetrics",
    "AlertRule",
    "AlertEvent",
    "CachePerformanceMetrics",
    "CacheEvent",
]
