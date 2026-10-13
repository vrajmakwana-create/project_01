from sqlalchemy import BigInteger, Boolean, Enum as SEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import LoginType
from app.db.models.base import IdMixins, TimeMixins


class User(IdMixins, TimeMixins):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String, nullable=True, default=None)
    last_name: Mapped[str] = mapped_column(String, nullable=True, default=None)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=True, default=None)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    otp: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    otp_expiry: Mapped[int] = mapped_column(BigInteger, nullable=True, default=None)
    login_type: Mapped[str] = mapped_column(
        SEnum(LoginType), nullable=True, default=LoginType.EMAIL.value
    )
    social_id: Mapped[str] = mapped_column(String, nullable=True, default=None)

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), nullable=False)

    user_sessions: Mapped["UserSession"] = relationship("UserSession", back_populates="user")
    user_info: Mapped["UserInformation"] = relationship("UserInformation", back_populates="user")
    role: Mapped["Role"] = relationship("Role", back_populates="user")

    # Resume Related Information
    personal_info_resume: Mapped["PersonalInfoResume"] = relationship("PersonalInfoResume", back_populates= "user")
    professional_summary_resume: Mapped["ProfessionalSummaryResume"] = relationship("ProfessionalSummaryResume",  back_populates= "user")
    educational_info_resume: Mapped["EducationalInfoResume"] = relationship("EducationalInfoResume", uselist = True, back_populates= "user")
    work_experience_resume: Mapped["WorkExperienceResume"] = relationship("WorkExperienceResume", uselist = True, back_populates= "user")
    skills_resume: Mapped["SkillResume"] = relationship("SkillResume", uselist = True, back_populates= "user")
    projects_info_resume: Mapped["ProjectInfoResume"] = relationship("ProjectInfoResume", uselist = True, back_populates= "user")