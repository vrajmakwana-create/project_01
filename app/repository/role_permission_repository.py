from app.repository.base_repository import BaseRepository
from app.db.models.role_permission import RolePermission
from app.db.models.permission import Permission
from sqlalchemy.orm import Session


class RolePermissionRepository(BaseRepository[RolePermission]):
    def __init__(self, db: Session):
        super().__init__(RolePermission, db)

    # Get Join with Permisison repo
    def get_permissions_from_role_id(self, role_id: str):
        return self.db.query(Permission.permission_name).join(RolePermission).filter(RolePermission.role_id == role_id).all()