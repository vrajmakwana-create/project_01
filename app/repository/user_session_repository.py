from app.repository.base_repository import BaseRepository
from app.db.models.user_session import UserSession
from sqlalchemy.ext.asyncio import AsyncSession


class UserSessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserSession, db)

    # Create or Update User Session asynchronously
    async def add_user_session(self, session_data: dict) -> UserSession:
        user_session = await self.get_by_field("user_id", session_data["user_id"])
        if user_session:
            user_session = await self.update(user_session, session_data)
        else:
            user_session = await self.create(session_data)
        return user_session