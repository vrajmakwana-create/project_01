from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User


class SkillResume(IdMixins, TimeMixins):
    __tablename__ = "skills_resume"

    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    is_original: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    # Relationships
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship("User", back_populates="skills_resume")

    def __str__(self):
        return f"SkillResume(user_id={self.user_id})"
