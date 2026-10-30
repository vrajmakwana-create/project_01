import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.permission import Permission
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_PERMISSIONS = ["create", "read", "update", "delete"]


async def seed_permissions(db: Optional[AsyncSession] = None):
    async def _execute(session: AsyncSession):
        for p_name in DEFAULT_PERMISSIONS:
            stmt = select(Permission).where(Permission.permission_name == p_name)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            if not existing:
                permission = Permission(permission_name=p_name)
                session.add(permission)
                logger.info(f"Permission '{p_name}' added.")
            else:
                logger.info(f"Permission '{p_name}' already exists.")
        await session.commit()
        logger.info("Permissions seeding completed.")

    if db is not None:
        await _execute(db)
    else:
        async with AsyncSessionLocal() as session:
            await _execute(session)


if __name__ == "__main__":
    asyncio.run(seed_permissions())
