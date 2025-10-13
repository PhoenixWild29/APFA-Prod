"""
User role assignment schemas
"""
from pydantic import BaseModel, Field
from typing import List


class UserRoleAssignment(BaseModel):
    """User role assignment request"""
    role_ids: List[str] = Field(..., description="List of role IDs to assign")


class UserRolesResponse(BaseModel):
    """User roles response"""
    user_id: str = Field(..., description="User identifier")
    roles: List[str] = Field(..., description="Assigned role IDs")

