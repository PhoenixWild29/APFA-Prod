"""
Role management schemas
"""
from pydantic import BaseModel, Field
from typing import Optional


class RoleCreate(BaseModel):
    """Role creation request"""
    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    description: str = Field(..., min_length=1, max_length=500, description="Role description")


class RoleUpdate(BaseModel):
    """Role update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=500)


class RoleResponse(BaseModel):
    """Role response"""
    role_id: str = Field(..., description="Unique role identifier")
    name: str = Field(..., description="Role name")
    description: str = Field(..., description="Role description")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

