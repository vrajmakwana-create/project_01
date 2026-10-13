from typing import Any
from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User


class ProjectInfoResume(IdMixins, TimeMixins):
    __tablename__ = "projects_info_resume"

    projects: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    is_original: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    # Relationships
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship("User", back_populates="projects_info_resume")

    def __str__(self):
        return f"ProjectInfoResume(user_id={self.user_id})"
