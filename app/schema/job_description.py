from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionAnalyzeRequest(BaseModel):
    job_description: str = Field(..., min_length=10, description="Raw text of the target job description")
    job_title: Optional[str] = Field(None, description="Job title if known or extracted")
    company_name: Optional[str] = Field(None, description="Hiring company name if known")


class InterviewPreparationTip(BaseModel):
    skill: str
    priority: Optional[str] = "High"
    why_important: Optional[str] = ""
    key_concepts_to_revise: List[str] = Field(default_factory=list)
    likely_interview_questions: List[str] = Field(default_factory=list)


class SkillsAnalysisResponse(BaseModel):
    total_jd_skills_count: int
    matching_skills_count: int
    missing_skills_count: int
    extracted_jd_skills: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)


class ExperienceSeniorityAnalysis(BaseModel):
    jd_experience_years: Optional[float] = None
    candidate_experience_years: Optional[float] = None
    seniority_level_jd: Optional[str] = None
    seniority_level_candidate: Optional[str] = None
    experience_gap_verdict: Optional[str] = None


class TailoredResumeResponse(BaseModel):
    tailored_summary: Optional[str] = None
    tailored_skills: List[str] = Field(default_factory=list)
    professional_summary_id: Optional[str] = None
    skill_id: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    match_score: int
    match_rationale: Optional[str] = None
    experience_analysis: ExperienceSeniorityAnalysis
    skills_analysis: SkillsAnalysisResponse
    interview_preparation: List[InterviewPreparationTip] = Field(default_factory=list)
    tailored_resume: TailoredResumeResponse
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionListItemResponse(BaseModel):
    id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    match_score: int
    seniority_level_jd: Optional[str] = None
    seniority_level_candidate: Optional[str] = None
    missing_skills_count: int
    created_at: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
