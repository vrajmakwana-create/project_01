from email.policy import default
from sqlalchemy import Boolean, ForeignKey, Integer
from app.db.models.user import User
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, BigInteger
from app.db.models.base import IdMixins, TimeMixins


class WorkExperienceResume(IdMixins, TimeMixins):
    __tablename__ = "work_experience_resume"

    # Job Title
    title: Mapped[str] = mapped_column(String, nullable=False)

    # Company Information
    company: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    location_typw: Mapped[str] = mapped_column(String, nullable = False)

    # Employment Type
    employment_type: Mapped[str] = mapped_column(String, nullable = False)

    # Job Status
    is_currently_work_here: Mapped[bool] = mapped_column(Boolean, nullable = False, default=False)
    
    # Time Period
    start_date: Mapped[str] = mapped_column(BigInteger, nullable = False)
    end_date: Mapped[str] = mapped_column(BigInteger, nullable = True, default = None)

    # Job Responsibilities
    responsibilities: Mapped[str] = mapped_column(String, nullable=False)

    # Achievements
    achievements: Mapped[str] = mapped_column(String, nullable=False)

    # Order
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(User, back_populates = "work_experience_resume")

    def __str__(self):
        return self.title
