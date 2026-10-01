from app.repository.base_repository import BaseRepository
from app.db.models.permission import Permission
from sqlalchemy.orm import Session


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: Session):
        super().__init__(Permission, db)
