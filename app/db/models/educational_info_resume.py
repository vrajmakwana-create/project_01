from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, ForeignKey, Boolean
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User


class EducationalInfoResume(IdMixins, TimeMixins):
    __tablename__ = "educational_info_resume"

    degree: Mapped[str] = mapped_column(String, nullable=False)
    institution: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[str] = mapped_column(BigInteger, nullable=False)
    end_date: Mapped[str] = mapped_column(BigInteger, nullable=True, default = None)
    gpa: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    
    user: Mapped[User] = relationship(User, back_populates = "educational_info_resume")

    def __str__(self):
        return self.degree
