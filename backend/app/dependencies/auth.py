import uuid
from typing import Set
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.exceptions.base import AuthenticationException, AuthorizationException
from app.models.user import User
from app.repositories.user import user_repository

# Security scheme wrapper
security_scheme = HTTPBearer(auto_error=False)

# RBAC permissions lookup map matching rbac.md definitions
ROLE_PERMISSIONS = {
    "admin": {
        "connect_provider", "disconnect_provider", "view_costs", "view_inventory",
        "apply_optimization", "dismiss_optimization", "read_chat", "write_chat",
        "export_reports", "manage_users", "view_audit_logs", "view_optimization",
        "view_billing", "run_copilot"
    },
    "operator": {
        "connect_provider", "view_costs", "view_inventory",
        "apply_optimization", "dismiss_optimization", "read_chat", "write_chat",
        "export_reports", "view_optimization", "view_billing", "run_copilot"
    },
    "billing_admin": {
        "view_costs", "view_inventory", "read_chat", "write_chat", "export_reports",
        "view_optimization", "view_billing", "run_copilot"
    },
    "viewer": {
        "view_costs", "view_inventory", "read_chat", "export_reports",
        "view_optimization", "view_billing", "run_copilot"
    }
}


async def get_current_user(
    token: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Parses, validates, and decodes the JWT access token from Authorization header.
    Fetches the active user record.
    """
    if not token:
        raise AuthenticationException("Authorization header token missing.")

    try:
        payload = jwt.decode(
            token.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify it is an access token
        if payload.get("type") != "access":
            raise AuthenticationException("Invalid token type. Expected access token.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationException("Token payload missing subject.")

        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError) as e:
        raise AuthenticationException("Access token signature verification failed.") from e

    user = await user_repository.get(db, user_id)
    if not user:
        raise AuthenticationException("User associated with token does not exist.")

    if not user.is_active:
        raise AuthenticationException("User account has been deactivated.")

    return user


class PermissionChecker:
    """
    Dependency checking user permissions based on their role mappings.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.lower()
        user_permissions: Set[str] = ROLE_PERMISSIONS.get(user_role, set())

        if self.required_permission not in user_permissions:
            raise AuthorizationException(
                f"Role '{current_user.role}' lacks required permission: '{self.required_permission}'"
            )

        return current_user
