from app.repository.base_repository import BaseRepository
from app.db.models.role import Role
from sqlalchemy.ext.asyncio import AsyncSession


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)
