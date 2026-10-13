from pydantic import BaseModel, ConfigDict
from typing import Optional

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

# Work Experience Schema
class WorkExperienceSchema(BaseModel):
    job_title: str
    company_name: str
    start_date: str
    end_date: str
    responsibilities: str

# Educational Info Schema
class EducationalInfoSchema(BaseModel):
    degree: str
    school_name: str
    start_date: str
    end_date: str
    gpa: str

# Projects Info Schema
class ProjectsInfoSchema(BaseModel):
    name: str
    description: str
    url: str
    start_date: int
    end_date: Optional[int] = None
    status: str
    responsibilities: str
    achievements: str
    order: int

# Skill Schema
class SkillSchema(BaseModel):
    name: str
    rate_skill: Optional[float] = None


# DATABASE MODELS SCHEMA

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

