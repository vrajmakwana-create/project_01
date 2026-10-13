from email.policy import default
from sqlalchemy import Boolean, ForeignKey
from app.db.models.user import User
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, BigInteger, Integer
from app.db.models.base import IdMixins, TimeMixins


class ProjectInfoResume(IdMixins, TimeMixins):
    __tablename__ = "projects_info_resume"

    # Project Name
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Project Description
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Project URL
    url: Mapped[str] = mapped_column(String, nullable=False)

    # Project Start Date
    start_date: Mapped[str] = mapped_column(BigInteger, nullable=False)

    # Project End Date
    end_date: Mapped[str] = mapped_column(BigInteger, nullable=True, default=None)

    # Project Status
    status: Mapped[str] = mapped_column(String, nullable=False)

    # Project Responsibilities
    responsibilities: Mapped[str] = mapped_column(String, nullable=False)

    # Project Achievements
    achievements: Mapped[str] = mapped_column(String, nullable=False)

    # Project Order
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    is_original: Mapped[bool] = mapped_column(Boolean, nullable = True, default = False)

    # Relationships
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(User, back_populates = "projects_info_resume")

    def __str__(self):
        return self.name
