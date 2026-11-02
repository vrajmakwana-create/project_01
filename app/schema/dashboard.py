from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DashboardKPIs(BaseModel):
    overall_resume_score: int = Field(..., description="Overall resume quality score from 0 to 100")
    ats_parsing_rate: int = Field(..., description="Estimated ATS readability and pass rate percentage (0 to 100)")
    tailored_applications_count: int = Field(..., description="Total tailored job descriptions / resumes generated")
    average_match_score: float = Field(..., description="Average ATS match score across all tailored applications")
    total_experience_years: float = Field(..., description="Total non-overlapping candidate experience in years")


class SectionStatus(BaseModel):
    personal_info: bool = False
    professional_summary: bool = False
    skills: bool = False
    work_experience: bool = False
    projects: bool = False
    education: bool = False


class PrimaryResumeData(BaseModel):
    target_role: Optional[str] = Field(None, description="Current or target professional role title")
    candidate_name: Optional[str] = Field(None, description="Full candidate name")
    year: Optional[int] = Field(None, description="Year of resume generation or last update")
    resume_url: Optional[str] = Field(None, description="Original generated resume PDF URL")
    last_updated_at: Optional[str] = Field(None, description="ISO timestamp of last profile update")
    completeness_score: int = Field(..., description="Percentage of resume sections completed (0 to 100)")
    sections_status: SectionStatus = Field(default_factory=SectionStatus)


class SkillsAnalytics(BaseModel):
    total_skills_count: int = 0
    populated_categories_count: int = 0
    skills_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    top_matching_market_skills: List[str] = Field(default_factory=list)
    top_missing_skills_for_interviews: List[str] = Field(default_factory=list)


class RecentApplicationItem(BaseModel):
    id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    match_score: int = 0
    seniority_level_jd: Optional[str] = None
    created_at: Optional[str] = None
    resume_url: Optional[str] = None


class MatchDistribution(BaseModel):
    high_match_80_plus: int = 0
    moderate_match_60_to_79: int = 0
    low_match_below_60: int = 0


class TailoredApplicationsAnalytics(BaseModel):
    total_count: int = 0
    match_distribution: MatchDistribution = Field(default_factory=MatchDistribution)
    recent_tailored_applications: List[RecentApplicationItem] = Field(default_factory=list)


class ActionableRecommendation(BaseModel):
    type: str = "content"
    priority: str = "Medium"
    message: str


class DashboardResponseData(BaseModel):
    kpis: DashboardKPIs
    primary_resume: PrimaryResumeData
    skills_analytics: SkillsAnalytics
    tailored_applications_analytics: TailoredApplicationsAnalytics
    actionable_recommendations: List[ActionableRecommendation] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

