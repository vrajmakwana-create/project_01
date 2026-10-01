from app.db.session import Session
from app.db.models.role import Role
from app.db.models.permission import Permission
from app.db.models.role_permission import RolePermission

ROLE_PERMISSIONS_MAPPING = {
    "admin": ["create", "read", "update", "delete"],
    "manager": ["update", "read"],
    "employee": ["read"],
    "employees": ["read"],
}


def seed_role_permissions():
    db = Session()
    try:
        for role_name, perm_names in ROLE_PERMISSIONS_MAPPING.items():
            role = db.query(Role).filter(Role.role_name == role_name).first()
            if not role:
                continue

            for p_name in perm_names:
                permission = db.query(Permission).filter(Permission.permission_name == p_name).first()
                if not permission:
                    continue

                existing = (
                    db.query(RolePermission)
                    .filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                    .first()
                )
                if not existing:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                    db.add(role_perm)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_role_permissions()
