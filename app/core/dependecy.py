"""Backward-compatible alias for app.core.dependencies."""
from app.core.dependencies import (
    security_scheme,
    validate_token,
    current_user,
    RoleCheck,
    PermissionCheck,
)

__all__ = [
    "security_scheme",
    "validate_token",
    "current_user",
    "RoleCheck",
    "PermissionCheck",
]
