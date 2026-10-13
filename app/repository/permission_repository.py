from app.repository.base_repository import BaseRepository
from app.db.models.permission import Permission
from sqlalchemy.ext.asyncio import AsyncSession


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)
