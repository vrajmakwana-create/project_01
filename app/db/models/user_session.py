from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from app.db.models.base import IdMixins, TimeMixins


class UserSession(IdMixins, TimeMixins):
    __tablename__ = "user_sessions"

    session: Mapped[str] = mapped_column(String)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship("User", back_populates="user_sessions")
