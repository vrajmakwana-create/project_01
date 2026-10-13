from typing import Any
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User


class EducationalInfoResume(IdMixins, TimeMixins):
    __tablename__ = "educational_info_resume"

    educations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

    user: Mapped["User"] = relationship("User", back_populates="educational_info_resume")

    def __str__(self):
        return f"EducationalInfoResume(user_id={self.user_id})"
