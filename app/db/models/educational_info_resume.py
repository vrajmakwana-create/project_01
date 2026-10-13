from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, ForeignKey, Boolean
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User
from typing import Any


class EducationalInfoResume(IdMixins, TimeMixins):
    __tablename__ = "educational_info_resume"

    educations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable = False)
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    
    user: Mapped[User] = relationship(User, back_populates = "educational_info_resume")

    def __str__(self):
        return self.degree
