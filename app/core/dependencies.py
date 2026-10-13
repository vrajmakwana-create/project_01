from typing import Optional
from fastapi import status as http_status, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.message import ErrorMessage
from app.core.jwt import verify_token
from app.repository.role_repository import RoleRepository
from app.repository.user_session_repository import UserSessionRepository
from app.repository.role_permission_repository import RolePermissionRepository

# Enables Swagger UI OpenAPI "Authorize" dialog in /docs
security_scheme = HTTPBearer(auto_error=False)


async def validate_token(
    request: Request,
    db: AsyncSession,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> dict:
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        bearer_token = request.headers.get("authorization")
        if not bearer_token:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.INVALID_TOKEN,
            )
        parts = bearer_token.strip().split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.INVALID_TOKEN,
            )
        token = parts[1]

    if not token:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.INVALID_TOKEN,
        )

    # Check active user session in DB asynchronously
    user_session_repo = UserSessionRepository(db)
    user_session = await user_session_repo.get_by_field("session", token)
    if not user_session:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.SESSION_EXPIRED,
        )

    return verify_token(token)


async def current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await validate_token(request, db, credentials)


class RoleCheck:
    def __init__(self, roles: list[str]):
        self.allowed_roles = roles

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        payload = await validate_token(request, db, credentials)
        role_id = payload.get("role_id", None)

        if not role_id:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.UNAUTHORIZED_ACCESS,
            )

        role_repo = RoleRepository(db)
        role_detail = await role_repo.get(role_id)
        if not role_detail:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.UNAUTHORIZED_ACCESS,
            )

        role_name = role_detail.role_name.strip()
        if role_name not in self.allowed_roles:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.UNAUTHORIZED_ACCESS,
            )

        return payload


class PermissionCheck:
    def __init__(self, permissions: list[str]):
        self.allowed_permissions = permissions

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        payload = await validate_token(request, db, credentials)
        role_id = payload.get("role_id", None)

        if not role_id:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.UNAUTHORIZED_ACCESS,
            )

        role_permission_repo = RolePermissionRepository(db)
        db_permissions = await role_permission_repo.get_permissions_from_role_id(role_id)

        if not db_permissions:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.UNAUTHORIZED_ACCESS,
            )

        permission_names = {permission[0] for permission in db_permissions}

        if not set(self.allowed_permissions).issubset(permission_names):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessage.UNAUTHORIZED_ACCESS,
            )

        return payload
