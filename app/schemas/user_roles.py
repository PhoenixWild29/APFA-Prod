"""
User role assignment schemas
"""

from typing import List

from pydantic import BaseModel, Field


class UserRoleAssignment(BaseModel):
    """User role assignment request"""

    role_ids: List[str] = Field(..., description="List of role IDs to assign")


class UserRolesResponse(BaseModel):
    """User roles response"""

    user_id: str = Field(..., description="User identifier")
    roles: List[str] = Field(..., description="Assigned role IDs")
