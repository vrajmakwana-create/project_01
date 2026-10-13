from email.policy import default
from sqlalchemy import Boolean, ForeignKey, Integer
from app.db.models.user import User
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, BigInteger
from app.db.models.base import IdMixins, TimeMixins
from typing import Any
from sqlalchemy.dialects.postgresql import JSONB

class WorkExperienceResume(IdMixins, TimeMixins):
    __tablename__ = "work_experience_resume"

    work_experience: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable = False)

    # Relationships
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(User, back_populates = "work_experience_resume")

    def __str__(self):
        return self.title
