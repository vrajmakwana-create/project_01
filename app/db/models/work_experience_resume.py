from typing import Any
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User


class WorkExperienceResume(IdMixins, TimeMixins):
    __tablename__ = "work_experience_resume"

    work_experience: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    # Relationships
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship("User", back_populates="work_experience_resume")

    def __str__(self):
        return f"WorkExperienceResume(user_id={self.user_id})"
