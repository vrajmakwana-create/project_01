from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from app.db.models.base import IdMixins, TimeMixins


class RolePermission(IdMixins, TimeMixins):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"))
    permission_id: Mapped[str] = mapped_column(ForeignKey("permissions.id"))

    def __str__(self):
        return self.role_name
