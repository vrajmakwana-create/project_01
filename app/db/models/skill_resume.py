from sqlalchemy.dialects.postgresql import JSONB
from email.policy import default
from sqlalchemy import Boolean, ForeignKey
from app.db.models.user import User
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, BigInteger, Integer, Float
from app.db.models.base import IdMixins, TimeMixins


class SkillResume(IdMixins, TimeMixins):
    __tablename__ = "skills_resume"

    # Skill Name
    skills: Mapped[list[str]] = mapped_column(JSONB, nullable = False)
    is_original: Mapped[bool] = mapped_column(Boolean, nullable = True, default = False)

    # Relationships
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(User, back_populates = "skills_resume")

    def __str__(self):
        return self.title
