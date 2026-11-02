import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.role import Role
from app.db.models.permission import Permission
from app.db.models.role_permission import RolePermission
from app.core.logger import get_logger

logger = get_logger(__name__)

ROLE_PERMISSIONS_MAPPING = {
    "admin": ["create", "read", "update", "delete"],
    "manager": ["update", "read"],
    "employee": ["read"],
    "employees": ["read"],
}


async def seed_role_permissions(db: Optional[AsyncSession] = None):
    async def _execute(session: AsyncSession):
        for role_name, perm_names in ROLE_PERMISSIONS_MAPPING.items():
            role_stmt = select(Role).where(Role.role_name == role_name)
            role_result = await session.execute(role_stmt)
            role = role_result.scalars().first()
            if not role:
                logger.warning(f"Role '{role_name}' not found. Skipping permissions mapping.")
                continue

            for p_name in perm_names:
                perm_stmt = select(Permission).where(Permission.permission_name == p_name)
                perm_result = await session.execute(perm_stmt)
                permission = perm_result.scalars().first()
                if not permission:
                    logger.warning(f"Permission '{p_name}' not found. Skipping.")
                    continue

                existing_stmt = select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
                existing_result = await session.execute(existing_stmt)
                existing = existing_result.scalars().first()
                if not existing:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                    session.add(role_perm)
                    logger.info(f"Assigned permission '{p_name}' to role '{role_name}'.")
                else:
                    logger.info(f"Permission '{p_name}' already assigned to role '{role_name}'.")
        await session.commit()
        logger.info("Role permissions seeding completed.")

    if db is not None:
        await _execute(db)
    else:
        async with AsyncSessionLocal() as session:
            await _execute(session)


if __name__ == "__main__":
    asyncio.run(seed_role_permissions())
