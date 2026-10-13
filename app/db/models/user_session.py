from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from app.db.models.base import IdMixins, TimeMixins


class UserSession(IdMixins, TimeMixins):
    __tablename__ = "user_sessions"

    session: Mapped[str] = mapped_column(String, index=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, index=True, nullable=False)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="user_sessions")
