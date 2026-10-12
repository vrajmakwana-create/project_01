from app.repository.base_repository import BaseRepository
from app.db.models.user_session import UserSession
from sqlalchemy.orm import Session


class UserSessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: Session):
        super().__init__(UserSession, db)

    # Create or Update User Session
    def add_user_session(self, session_data: dict) -> UserSession:
        user_session = self.get_by_field("user_id", session_data["user_id"])
        if user_session:
            user_session = self.update(user_session, session_data)
        else:
            user_session = self.create(session_data)
        return user_session
    


    
    