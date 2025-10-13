"""
Core RBAC (Role-Based Access Control) data models

Provides foundational data structures for:
- Role definitions and management
- Permission specifications
- User role assignments
- Access control hierarchy
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RoleName(str, Enum):
    """Standard role names"""
    STANDARD_USER = "standard_user"
    FINANCIAL_ADVISOR = "financial_advisor"
    ADMINISTRATOR = "administrator"


class PermissionResource(str, Enum):
    """Permission resource types"""
    DOCUMENTS = "documents"
    ADVICE = "advice"
    ADMIN = "admin"
    USERS = "users"


class PermissionAction(str, Enum):
    """Permission action types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage"


class Role(BaseModel):
    """
    Role data model for RBAC
    
    Defines a role with associated permissions and hierarchy.
    
    Attributes:
        role_id: Unique role identifier
        name: Role name (standard values or custom)
        description: Role description
        permissions: List of permission identifiers
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_active: Whether role is currently active
        hierarchy_level: Role hierarchy level (higher = more privileged)
    
    Example:
        >>> role = Role(
        ...     role_id="role_admin",
        ...     name="administrator",
        ...     description="Full system access",
        ...     permissions=["perm_1", "perm_2"],
        ...     hierarchy_level=10
        ... )
    """
    role_id: str = Field(
        ...,
        description="Unique role identifier",
        min_length=1,
        max_length=255
    )
    name: str = Field(
        ...,
        description="Role name",
        min_length=1,
        max_length=100
    )
    description: str = Field(
        ...,
        description="Role description",
        max_length=500
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="List of permission identifiers"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    is_active: bool = Field(
        default=True,
        description="Whether role is active"
    )
    hierarchy_level: int = Field(
        ...,
        description="Role hierarchy level (higher = more privileged)",
        ge=0,
        le=100
    )
    
    @field_validator('created_at', 'updated_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamps are timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "role_id": "role_550e8400-e29b-41d4-a716-446655440000",
                "name": "administrator",
                "description": "Full system access with all permissions",
                "permissions": ["perm_advice_generate", "perm_admin_celery", "perm_users_manage"],
                "created_at": "2025-10-11T14:30:00Z",
                "updated_at": "2025-10-11T14:30:00Z",
                "is_active": True,
                "hierarchy_level": 10
            }
        }


class Permission(BaseModel):
    """
    Permission data model for RBAC
    
    Defines a specific permission with resource and action.
    
    Attributes:
        permission_id: Unique permission identifier
        name: Permission name (e.g., "advice:generate")
        resource: Resource type (documents, advice, admin, users)
        action: Action type (read, write, delete, manage)
        description: Permission description
        created_at: Creation timestamp
        is_active: Whether permission is active
    
    Example:
        >>> permission = Permission(
        ...     permission_id="perm_123",
        ...     name="advice:generate",
        ...     resource="advice",
        ...     action="write",
        ...     description="Generate financial advice"
        ... )
    """
    permission_id: str = Field(
        ...,
        description="Unique permission identifier",
        min_length=1,
        max_length=255
    )
    name: str = Field(
        ...,
        description="Permission name (e.g., advice:generate)",
        min_length=1,
        max_length=100
    )
    resource: PermissionResource = Field(
        ...,
        description="Resource type"
    )
    action: PermissionAction = Field(
        ...,
        description="Action type"
    )
    description: str = Field(
        ...,
        description="Permission description",
        max_length=500
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    is_active: bool = Field(
        default=True,
        description="Whether permission is active"
    )
    
    @field_validator('created_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "permission_id": "perm_550e8400-e29b-41d4-a716-446655440000",
                "name": "advice:generate",
                "resource": "advice",
                "action": "write",
                "description": "Generate personalized financial advice",
                "created_at": "2025-10-11T14:30:00Z",
                "is_active": True
            }
        }


class UserRoleAssignment(BaseModel):
    """
    User role assignment data model
    
    Tracks role assignments to users with metadata and expiration.
    
    Attributes:
        assignment_id: Unique assignment identifier
        user_id: User identifier
        role_id: Role identifier
        assigned_by: User ID who assigned the role
        assigned_at: Assignment timestamp
        expires_at: Optional expiration timestamp
        is_active: Whether assignment is active
        assignment_metadata: Additional assignment metadata
    
    Example:
        >>> assignment = UserRoleAssignment(
        ...     assignment_id="assign_123",
        ...     user_id="user_john",
        ...     role_id="role_advisor",
        ...     assigned_by="user_admin"
        ... )
    """
    assignment_id: str = Field(
        ...,
        description="Unique assignment identifier",
        min_length=1,
        max_length=255
    )
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    role_id: str = Field(
        ...,
        description="Role identifier",
        min_length=1,
        max_length=255
    )
    assigned_by: str = Field(
        ...,
        description="User ID who assigned the role",
        min_length=1,
        max_length=255
    )
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Assignment timestamp"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Optional expiration timestamp"
    )
    is_active: bool = Field(
        default=True,
        description="Whether assignment is active"
    )
    assignment_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional assignment metadata",
        examples=[{
            "reason": "Promoted to advisor",
            "department": "financial_services",
            "approval_ticket": "TKT-12345"
        }]
    )
    
    @field_validator('assigned_at', 'expires_at')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure timestamps are timezone-aware"""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('expires_at')
    @classmethod
    def validate_expiration_after_assignment(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure expiration is after assignment"""
        if v:
            assigned_at = info.data.get('assigned_at')
            if assigned_at and v <= assigned_at:
                raise ValueError("expires_at must be after assigned_at")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "assignment_id": "assign_550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_12345",
                "role_id": "role_advisor",
                "assigned_by": "user_admin",
                "assigned_at": "2025-10-11T14:30:00Z",
                "expires_at": None,
                "is_active": True,
                "assignment_metadata": {
                    "reason": "Promoted to financial advisor",
                    "department": "wealth_management",
                    "approval_ticket": "TKT-54321"
                }
            }
        }

