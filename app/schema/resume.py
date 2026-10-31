from typing import Any, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


# Personal Info Schema
class PersonalInfoSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    website: str
    github: str
    linkedin: str
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PersonalInfoUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None


# Professional Summary Schema
class ProfessionalSummarySchema(BaseModel):
    summary: str
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Technical Skill Categories
TECHNICAL_SKILL_CATEGORIES = [
    "Programming Languages",
    "Frameworks & Libraries",
    "Databases",
    "Tools & Technologies",
    "Cloud & DevOps",
    "Web Development",
    "AI & Machine Learning",
    "Data Analysis & Visualization",
    "Testing & QA",
    "Operating Systems",
]


class CategorizedSkillItem(BaseModel):
    category: str
    skills: list[str]

    model_config = ConfigDict(from_attributes=True, extra="allow")


# Skill Schema (Supports categorized dict, list of categorized items, or flat list of strings)
class SkillSchema(BaseModel):
    skills: Union[dict[str, list[str]], list[CategorizedSkillItem], list[str]]
    user_id: Optional[str] = None
    is_original: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def wrap_skills_payload(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"skills": data}
        if isinstance(data, dict):
            if "skills" not in data:
                user_id = data.pop("user_id", None)
                is_orig = data.pop("is_original", False)
                return {"skills": data, "user_id": user_id, "is_original": is_orig}
        return data


# Educational Info Schema
class EducationItemSchema(BaseModel):
    degree: str
    institution: Optional[str] = None
    school_name: Optional[str] = None
    start_date: Optional[Union[str, int]] = None
    end_date: Optional[Union[str, int]] = None
    gpa: Optional[str] = None
    field_of_study: Optional[str] = None
    url: Optional[str] = None
    order: Optional[Union[int, str]] = None
    is_current: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def normalize_institution(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "school_name" in data and not data.get("institution"):
                data["institution"] = data["school_name"]
            elif "institution" in data and not data.get("school_name"):
                data["school_name"] = data["institution"]
        return data


class EducationalInfoSchema(BaseModel):
    educations: list[EducationItemSchema]
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def wrap_educations(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"educations": data}
        if isinstance(data, dict):
            if "educations" not in data:
                if "degree" in data or "school_name" in data or "institution" in data:
                    user_id = data.get("user_id")
                    item = {k: v for k, v in data.items() if k != "user_id"}
                    return {"educations": [item], "user_id": user_id}
        return data


# Work Experience Schema
class WorkExperienceItemSchema(BaseModel):
    job_title: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    location_type: Optional[str] = None
    employment_type: Optional[str] = None
    is_currently_work_here: Optional[bool] = False
    start_date: Optional[Union[str, int]] = None
    end_date: Optional[Union[str, int]] = None
    responsibilities: Optional[Union[str, list[str]]] = None
    achievements: Optional[Union[str, list[str]]] = None
    order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "job_title" in data and not data.get("title"):
                data["title"] = data["job_title"]
            elif "title" in data and not data.get("job_title"):
                data["job_title"] = data["title"]
            if "company_name" in data and not data.get("company"):
                data["company"] = data["company_name"]
            elif "company" in data and not data.get("company_name"):
                data["company_name"] = data["company"]
        return data


class WorkExperienceSchema(BaseModel):
    work_experience: list[WorkExperienceItemSchema]
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def wrap_work_experience(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"work_experience": data}
        if isinstance(data, dict):
            if "work_experience" not in data:
                if (
                    "job_title" in data
                    or "title" in data
                    or "company" in data
                    or "company_name" in data
                ):
                    user_id = data.get("user_id")
                    item = {k: v for k, v in data.items() if k != "user_id"}
                    return {"work_experience": [item], "user_id": user_id}
        return data


# Projects Info Schema
class ProjectItemSchema(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    start_date: Optional[Union[str, int]] = None
    end_date: Optional[Union[str, int]] = None
    status: Optional[str] = None
    responsibilities: Optional[Union[str, list[str]]] = None
    achievements: Optional[Union[str, list[str]]] = None
    order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ProjectsInfoSchema(BaseModel):
    projects: list[ProjectItemSchema]
    is_original: Optional[bool] = False
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def wrap_projects(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"projects": data}
        if isinstance(data, dict):
            if "projects" not in data:
                if "name" in data:
                    user_id = data.get("user_id")
                    is_original = data.get("is_original", False)
                    item = {k: v for k, v in data.items() if k not in ("user_id", "is_original")}
                    return {"projects": [item], "is_original": is_original, "user_id": user_id}
        return data


# DATABASE MODELS SCHEMA (Retained for backwards compatibility)
class ProjectInfoDBSchema(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    start_date: int
    end_date: Optional[int] = None
    status: str
    responsibilities: str
    achievements: str
    order: int


class EducationalInfoDBSchema(BaseModel):
    degree: str
    institution: Optional[str] = None
    url: Optional[str] = None
    start_date: int
    end_date: int
    gpa: str
    order: str


class WorkExperienceDBSchema(BaseModel):
    title: str
    company: str
    city: str
    state: str
    country: str
    location_type: str
    employment_type: str
    is_currently_work_here: bool = False
    start_date: int
    end_date: Optional[int] = None
    responsibilities: str
    achievements: str
    order: int

    model_config = ConfigDict(from_attributes=True)


class FullResumeSchema(BaseModel):
    personal_info: Optional[PersonalInfoSchema] = None
    professional_summary: Optional[ProfessionalSummarySchema] = None
    skills: Optional[SkillSchema] = None
    educational_info: Optional[EducationalInfoSchema] = None
    work_experience: Optional[WorkExperienceSchema] = None
    projects_info: Optional[ProjectsInfoSchema] = None

    model_config = ConfigDict(from_attributes=True)


class ImproveSummaryRequest(BaseModel):
    summary: Optional[str] = Field(
        default=None,
        description="Current resume summary text to improve and polish. If omitted, the user's saved summary from database will be used.",
    )
    tone: Optional[str] = Field(
        default="executive",
        description="Desired tone for the resume executive summary (e.g., executive, professional, impactful, concise, technical).",
    )

    model_config = ConfigDict(from_attributes=True)


class ImproveSummaryResponse(BaseModel):
    original_summary: str
    improved_summary: str
    tone: str
    key_strengths: list[str] = Field(default_factory=list)
    variations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
