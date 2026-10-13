from sqlalchemy import Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from app.db.models.base import IdMixins, TimeMixins
from app.db.models.user import User


class ProfessionalSummaryResume(IdMixins, TimeMixins):
    __tablename__ = "professional_summary_resume"

    summary: Mapped[str] = mapped_column(String, nullable=False)
    is_original: Mapped[bool] = mapped_column(Boolean, nullable = True, default=False)

    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    user: Mapped[User] = relationship(User, back_populates = "professional_summary_resume")

    def __str__(self):
        return self.summary
