from app.repository.base_repository import BaseRepository
from app.db.models.role import Role
from sqlalchemy.orm import Session


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(Role, db)
