from email.policy import default
from sqlalchemy import Boolean, ForeignKey
from typing import Any
from app.db.models.user import User
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, BigInteger, Integer
from app.db.models.base import IdMixins, TimeMixins
from app.schema.resume import ProjectInfoDBSchema
from sqlalchemy.dialects.postgresql import JSONB


class ProjectInfoResume(IdMixins, TimeMixins):
    __tablename__ = "projects_info_resume"

    projects: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable = False) 
    is_original: Mapped[bool] = mapped_column(Boolean, nullable = True, default = False)

    # Relationships
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(User, back_populates = "projects_info_resume")

    def __str__(self):
        return self.name
