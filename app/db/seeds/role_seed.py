import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.role import Role
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_ROLES = ["admin", "manager", "employee"]


async def seed_roles(db: Optional[AsyncSession] = None):
    async def _execute(session: AsyncSession):
        for r_name in DEFAULT_ROLES:
            stmt = select(Role).where(Role.role_name == r_name)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            if not existing:
                role = Role(role_name=r_name)
                session.add(role)
                logger.info(f"Role '{r_name}' added.")
            else:
                logger.info(f"Role '{r_name}' already exists.")
        await session.commit()
        logger.info("Roles seeding completed.")

    if db is not None:
        await _execute(db)
    else:
        async with AsyncSessionLocal() as session:
            await _execute(session)


if __name__ == "__main__":
    asyncio.run(seed_roles())
