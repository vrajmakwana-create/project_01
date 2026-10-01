from app.db.session import Session
from app.db.models.role import Role

DEFAULT_ROLES = ["admin", "manager", "employee"]


def seed_roles():
    db = Session()
    try:
        for r_name in DEFAULT_ROLES:
            existing = db.query(Role).filter(Role.role_name == r_name).first()
            if not existing:
                role = Role(role_name=r_name)
                db.add(role)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()
