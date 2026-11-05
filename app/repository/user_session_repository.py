from typing import Optional
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

    # Empty user session upon logout
    async def empty_user_session(self, user_id: str, token: Optional[str] = None) -> None:
        user_sessions = await self.get_all(filters={"user_id": user_id}, active_only=False)
        if not user_sessions:
            single = await self.get_by_field("user_id", user_id)
            if single:
                user_sessions = [single]
            elif token:
                token_session = await self.get_by_field("session", token)
                if token_session:
                    user_sessions = [token_session]

        for session_item in user_sessions:
            session_item.session = ""
            session_item.refresh_token = ""

        if user_sessions:
            await self.db.commit()
