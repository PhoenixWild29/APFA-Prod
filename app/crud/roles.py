"""
CRUD operations for role management
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

# In-memory role storage (in production, use database)
roles_db: Dict[str, dict] = {
    "role_admin": {
        "role_id": "role_admin",
        "name": "admin",
        "description": "Administrator with full system access",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    "role_advisor": {
        "role_id": "role_advisor",
        "name": "advisor",
        "description": "Financial advisor with client management access",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    "role_standard": {
        "role_id": "role_standard",
        "name": "standard",
        "description": "Standard user with basic access",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
}


def create_role(name: str, description: str) -> dict:
    """
    Create new role
    
    Args:
        name: Role name (must be unique)
        description: Role description
    
    Returns:
        Created role dict
    
    Raises:
        ValueError: If role name already exists
    """
    # Check for duplicate
    for role in roles_db.values():
        if role["name"].lower() == name.lower():
            raise ValueError(f"Role '{name}' already exists")
    
    role_id = f"role_{uuid.uuid4()}"
    now = datetime.now(timezone.utc).isoformat()
    
    role = {
        "role_id": role_id,
        "name": name,
        "description": description,
        "created_at": now,
        "updated_at": now,
    }
    
    roles_db[role_id] = role
    return role


def get_all_roles() -> List[dict]:
    """Get all roles"""
    return list(roles_db.values())


def get_role_by_id(role_id: str) -> Optional[dict]:
    """Get role by ID"""
    return roles_db.get(role_id)


def update_role(role_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[dict]:
    """
    Update role
    
    Args:
        role_id: Role ID to update
        name: New role name (optional)
        description: New description (optional)
    
    Returns:
        Updated role dict or None if not found
    
    Raises:
        ValueError: If new name conflicts with existing role
    """
    role = roles_db.get(role_id)
    if not role:
        return None
    
    # Check name uniqueness if changing name
    if name and name != role["name"]:
        for other_role in roles_db.values():
            if other_role["role_id"] != role_id and other_role["name"].lower() == name.lower():
                raise ValueError(f"Role '{name}' already exists")
        role["name"] = name
    
    if description:
        role["description"] = description
    
    role["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return role


def delete_role(role_id: str) -> bool:
    """
    Delete role
    
    Args:
        role_id: Role ID to delete
    
    Returns:
        True if deleted, False if not found
    """
    if role_id in roles_db:
        del roles_db[role_id]
        return True
    return False

