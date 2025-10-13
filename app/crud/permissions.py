"""
CRUD operations for permission management
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

# In-memory permission storage
permissions_db: Dict[str, dict] = {
    "perm_advice_generate": {
        "permission_id": "perm_advice_generate",
        "name": "advice:generate",
        "description": "Generate financial advice",
        "resource_identifier": "advice",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    "perm_advice_view": {
        "permission_id": "perm_advice_view",
        "name": "advice:view_history",
        "description": "View advice history",
        "resource_identifier": "advice",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    "perm_admin_celery": {
        "permission_id": "perm_admin_celery",
        "name": "admin:celery:manage",
        "description": "Manage Celery tasks",
        "resource_identifier": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
}

# Role-Permission associations
role_permissions_db: Dict[str, List[str]] = {
    "role_admin": ["perm_advice_generate", "perm_advice_view", "perm_admin_celery"],
    "role_advisor": ["perm_advice_generate", "perm_advice_view"],
    "role_standard": ["perm_advice_generate"],
}


def create_permission(name: str, description: str, resource_identifier: str) -> dict:
    """Create new permission"""
    # Check for duplicate
    for perm in permissions_db.values():
        if perm["name"].lower() == name.lower():
            raise ValueError(f"Permission '{name}' already exists")
    
    permission_id = f"perm_{uuid.uuid4()}"
    
    permission = {
        "permission_id": permission_id,
        "name": name,
        "description": description,
        "resource_identifier": resource_identifier,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    permissions_db[permission_id] = permission
    return permission


def get_all_permissions() -> List[dict]:
    """Get all permissions"""
    return list(permissions_db.values())


def get_permission_by_id(permission_id: str) -> Optional[dict]:
    """Get permission by ID"""
    return permissions_db.get(permission_id)


def assign_permissions_to_role(role_id: str, permission_ids: List[str]) -> List[dict]:
    """Assign permissions to role"""
    # Validate all permissions exist
    for perm_id in permission_ids:
        if perm_id not in permissions_db:
            raise ValueError(f"Permission '{perm_id}' not found")
    
    # Add to role-permission mapping
    if role_id not in role_permissions_db:
        role_permissions_db[role_id] = []
    
    # Add new permissions (avoid duplicates)
    for perm_id in permission_ids:
        if perm_id not in role_permissions_db[role_id]:
            role_permissions_db[role_id].append(perm_id)
    
    # Return permission details
    return [permissions_db[pid] for pid in role_permissions_db[role_id]]


def get_role_permissions(role_id: str) -> List[dict]:
    """Get all permissions for a role"""
    permission_ids = role_permissions_db.get(role_id, [])
    return [permissions_db[pid] for pid in permission_ids if pid in permissions_db]


def remove_permission_from_role(role_id: str, permission_id: str) -> bool:
    """Remove permission from role"""
    if role_id not in role_permissions_db:
        return False
    
    if permission_id in role_permissions_db[role_id]:
        role_permissions_db[role_id].remove(permission_id)
        return True
    
    return False

