import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def seed_all(db: Optional[AsyncSession] = None):
    """Seed roles, permissions, and role-permission mappings sequentially."""
    from app.db.seeds.role_seed import seed_roles
    from app.db.seeds.permission_seed import seed_permissions
    from app.db.seeds.role_permission_seed import seed_role_permissions

    if db is not None:
        await seed_roles(db)
        await seed_permissions(db)
        await seed_role_permissions(db)
    else:
        async with AsyncSessionLocal() as session:
            await seed_roles(session)
            await seed_permissions(session)
            await seed_role_permissions(session)


if __name__ == "__main__":
    asyncio.run(seed_all())
