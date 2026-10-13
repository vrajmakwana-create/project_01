from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.base_repository import BaseRepository
from app.db.models.role_permission import RolePermission
from app.db.models.permission import Permission


class RolePermissionRepository(BaseRepository[RolePermission]):
    def __init__(self, db: AsyncSession):
        super().__init__(RolePermission, db)

    # Get Join with Permission repo asynchronously
    async def get_permissions_from_role_id(self, role_id: str):
        stmt = (
            select(Permission.permission_name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self.db.execute(stmt)
        return result.all()