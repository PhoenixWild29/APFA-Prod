"""
Permission management schemas
"""
from pydantic import BaseModel, Field
from typing import List


class PermissionCreate(BaseModel):
    """Permission creation request"""
    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    description: str = Field(..., min_length=1, max_length=500, description="Permission description")
    resource_identifier: str = Field(..., min_length=1, max_length=50, description="Resource identifier")


class PermissionResponse(BaseModel):
    """Permission response"""
    permission_id: str = Field(..., description="Unique permission identifier")
    name: str = Field(..., description="Permission name")
    description: str = Field(..., description="Permission description")
    resource_identifier: str = Field(..., description="Resource identifier")
    created_at: str = Field(..., description="Creation timestamp")


class RolePermissionAssignment(BaseModel):
    """Role-permission assignment request"""
    permission_ids: List[str] = Field(..., description="List of permission IDs to assign")

