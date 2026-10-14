from typing import Optional, List, Dict, Any
from sqlalchemy import ForeignKey, String, Text, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.models.base import IdMixins, TimeMixins


class JobDescription(IdMixins, TimeMixins):
    __tablename__ = "job_descriptions"

    job_title: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    company_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    match_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Experience & Seniority Gap Analysis
    jd_experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    candidate_experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    seniority_level_jd: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    seniority_level_candidate: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    experience_gap_verdict: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Skills Analysis
    extracted_jd_skills: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    matching_skills: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    missing_skills: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    interview_preparation_tips: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    # Tailored Content
    tailored_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    tailored_skills: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    professional_summary_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("professional_summary_resume.id", ondelete="SET NULL"), nullable=True, default=None
    )
    skill_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("skills_resume.id", ondelete="SET NULL"), nullable=True, default=None
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="job_descriptions")
    professional_summary_resume: Mapped[Optional["ProfessionalSummaryResume"]] = relationship(
        "ProfessionalSummaryResume", back_populates="job_descriptions"
    )
    skills_resume: Mapped[Optional["SkillResume"]] = relationship(
        "SkillResume", back_populates="job_descriptions"
    )

    def __str__(self):
        return f"JobDescription(id={self.id}, user_id={self.user_id}, score={self.match_score})"
