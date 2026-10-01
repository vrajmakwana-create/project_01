from app.db.session import Session
from app.db.models.permission import Permission

DEFAULT_PERMISSIONS = ["create", "read", "update", "delete"]


def seed_permissions():
    db = Session()
    try:
        for p_name in DEFAULT_PERMISSIONS:
            existing = db.query(Permission).filter(Permission.permission_name == p_name).first()
            if not existing:
                permission = Permission(permission_name=p_name)
                db.add(permission)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_permissions()
