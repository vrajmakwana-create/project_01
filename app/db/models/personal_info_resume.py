from app.db.models.user import User
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from app.db.models.base import IdMixins, TimeMixins


class PersonalInfoResume(IdMixins, TimeMixins):
    __tablename__ = "personal_info_resume"

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    zip_code: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str] = mapped_column(String, nullable=False)
    github: Mapped[str] = mapped_column(String, nullable=False)
    linkedin: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    user: Mapped[User] = relationship(User, back_populates = "personal_info_resume")

    def __str__(self):
        return self.first_name + " " + self.last_name
