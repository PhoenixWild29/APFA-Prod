"""
CRUD operations for user role assignments
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

# In-memory user-role assignment storage
user_roles_db: Dict[str, List[str]] = {
    "testuser": ["role_standard"],
    "johndoe": ["role_advisor"],
    "admin": ["role_admin"],
}

# User-to-role assignment audit trail
assignment_audit: List[dict] = []


def assign_roles_to_user(user_id: str, role_ids: List[str], assigned_by: str) -> List[str]:
    """
    Assign roles to user
    
    Args:
        user_id: User identifier
        role_ids: List of role IDs to assign
        assigned_by: Admin user making the assignment
    
    Returns:
        List of role IDs now assigned to user
    
    Raises:
        ValueError: If role already assigned
    """
    if user_id not in user_roles_db:
        user_roles_db[user_id] = []
    
    current_roles = user_roles_db[user_id]
    
    for role_id in role_ids:
        if role_id in current_roles:
            raise ValueError(f"Role '{role_id}' already assigned to user '{user_id}'")
        
        current_roles.append(role_id)
        
        # Audit trail
        assignment_audit.append({
            "user_id": user_id,
            "role_id": role_id,
            "action": "assigned",
            "assigned_by": assigned_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return current_roles


def get_user_roles(user_id: str) -> List[str]:
    """Get all roles assigned to user"""
    return user_roles_db.get(user_id, [])


def remove_role_from_user(user_id: str, role_id: str, removed_by: str) -> bool:
    """Remove role from user"""
    if user_id not in user_roles_db:
        return False
    
    if role_id in user_roles_db[user_id]:
        user_roles_db[user_id].remove(role_id)
        
        # Audit trail
        assignment_audit.append({
            "user_id": user_id,
            "role_id": role_id,
            "action": "removed",
            "removed_by": removed_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return True
    
    return False


def replace_user_roles(user_id: str, role_ids: List[str], assigned_by: str) -> List[str]:
    """Replace all user roles with new set"""
    # Clear existing roles
    user_roles_db[user_id] = []
    
    # Assign new roles
    for role_id in role_ids:
        user_roles_db[user_id].append(role_id)
    
    # Audit trail
    assignment_audit.append({
        "user_id": user_id,
        "action": "replaced",
        "new_roles": role_ids,
        "assigned_by": assigned_by,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return user_roles_db[user_id]


def get_users_with_role(role_id: str) -> List[str]:
    """Get all users with a specific role"""
    users = []
    for user_id, roles in user_roles_db.items():
        if role_id in roles:
            users.append(user_id)
    return users

