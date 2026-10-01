from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String
from app.db.models.base import IdMixins, TimeMixins


class Role(IdMixins, TimeMixins):
    __tablename__ = "roles"

    role_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    user: Mapped["User"] = relationship("User", back_populates="role")

    def __str__(self):
        return self.role_name
