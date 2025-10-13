"""
Data models for APFA application

This package contains Pydantic data models for:
- Authentication and login events
- User profiles and sessions
- Security monitoring and alerts
- User registration and verification
"""
from app.models.login_events import LoginEvent, WebSocketLoginMessage
from app.models.auth_events import AuthenticationEvent, WebSocketAuthMessage
from app.models.user_profile import UserProfile, SessionMetadata
from app.models.user_registration import (
    UserRegistrationRequest,
    RegistrationResponse,
    RegistrationEvent,
    WebSocketRegistrationMessage
)
from app.models.user_login import UserLoginRequest, LoginResponse
from app.models.token_models import (
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenRevocationRequest,
    TokenEvent,
    WebSocketTokenMessage,
    TokenMetadata,
    TokenValidationResult
)
from app.models.document_processing import DocumentProcessingEvent, WebSocketDocumentMessage
from app.models.document_management import Document, BatchProgress, DocumentBatch
from app.models.faiss_models import IndexPerformanceMetrics, FAISSIndexMetadata
from app.models.document_upload import DocumentMetadata, UploadStatus, UploadState
from app.models.rbac import Role, Permission, UserRoleAssignment
from app.models.rbac_events import RBACEvent, WebSocketRBACMessage
from app.models.access_control import AccessRequest, AccessDecision
from app.models.celery_tasks import EmbeddingBatchTask, IndexBuildTask, TaskStatus, TaskStatusEnum
from app.models.document_batch import DocumentBatch, ProcessingOptions
from app.models.embedding_models import EmbeddingBatch, VectorEmbedding
from app.models.performance_tracking import (
    CachedAdviceResponse,
    ResponseMetrics,
    CacheMetadata,
    CacheInteraction,
    AgentExecutionStep
)
from app.models.advice_response import OptimizedAdviceResponse, BiasDetectionResults
from app.models.monitoring_events import SystemMetricsEvent, WebSocketMetricsMessage
from app.models.performance_snapshot import PerformanceSnapshot, SystemResourceMetrics
from app.models.alert_models import AlertRule, AlertEvent
from app.models.cache_performance import CachePerformanceMetrics, CacheEvent

__all__ = [
    'LoginEvent',
    'WebSocketLoginMessage',
    'AuthenticationEvent',
    'WebSocketAuthMessage',
    'UserProfile',
    'SessionMetadata',
    'UserRegistrationRequest',
    'RegistrationResponse',
    'RegistrationEvent',
    'WebSocketRegistrationMessage',
    'UserLoginRequest',
    'LoginResponse',
    'TokenRefreshRequest',
    'TokenRefreshResponse',
    'TokenRevocationRequest',
    'TokenEvent',
    'WebSocketTokenMessage',
    'TokenMetadata',
    'TokenValidationResult',
    'DocumentProcessingEvent',
    'WebSocketDocumentMessage',
    'Document',
    'BatchProgress',
    'DocumentBatch',
    'IndexPerformanceMetrics',
    'FAISSIndexMetadata',
    'DocumentMetadata',
    'UploadStatus',
    'UploadState',
    'Role',
    'Permission',
    'UserRoleAssignment',
    'RBACEvent',
    'WebSocketRBACMessage',
    'AccessRequest',
    'AccessDecision',
    'EmbeddingBatchTask',
    'IndexBuildTask',
    'TaskStatus',
    'TaskStatusEnum',
    'DocumentBatch',
    'ProcessingOptions',
    'EmbeddingBatch',
    'VectorEmbedding',
    'CachedAdviceResponse',
    'ResponseMetrics',
    'CacheMetadata',
    'CacheInteraction',
    'AgentExecutionStep',
    'OptimizedAdviceResponse',
    'BiasDetectionResults',
    'SystemMetricsEvent',
    'WebSocketMetricsMessage',
    'PerformanceSnapshot',
    'SystemResourceMetrics',
    'AlertRule',
    'AlertEvent',
    'CachePerformanceMetrics',
    'CacheEvent',
]

