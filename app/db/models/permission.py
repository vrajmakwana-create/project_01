from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String
from app.db.models.base import IdMixins, TimeMixins


class Permission(IdMixins, TimeMixins):
    __tablename__ = "permissions"

    permission_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    permission_description: Mapped[str] = mapped_column(String, nullable = True, default = None)

    def __str__(self):
        return self.permission_name
