from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.resume import (
    SkillSchema,
    PersonalInfoSchema,
    ProfessionalSummarySchema,
    PersonalInfoUpdateSchema,
    EducationalInfoSchema,
    WorkExperienceSchema,
    ProjectsInfoSchema,
)
from app.core.dependencies import current_user
from app.db.session import get_db
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resume", tags=["Resume"])


# ============================================================================
# RESUME FILE UPLOAD
# ============================================================================

@router.post("/upload")
async def upload_resume(
    request: Request, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.upload_resume(user["user_id"], file)


# ============================================================================
# PERSONAL INFO
# ============================================================================

@router.post("/save-personal-info")
async def save_personal_info(
    request: Request, 
    personal_info: PersonalInfoSchema, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_personal_info(personal_info, user["user_id"])


@router.patch("/update-personal-info")
async def update_personal_info(
    request: Request, 
    personal_info: PersonalInfoUpdateSchema, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_personal_info(personal_info, user["user_id"])


@router.get("/personal-info")
async def get_personal_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_personal_info(user["user_id"])


@router.delete("/personal-info")
async def delete_personal_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.delete_personal_info(user["user_id"])


# ============================================================================
# PROFESSIONAL SUMMARY
# ============================================================================

@router.post("/save-professional-summary")
async def save_professional_summary(
    request: Request, 
    personal_summary: ProfessionalSummarySchema, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_professional_summary(personal_summary, user["user_id"])


@router.patch("/update-professional-summary")
async def update_professional_summary(
    request: Request, 
    personal_summary: ProfessionalSummarySchema, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_professional_summary(personal_summary, user["user_id"])


@router.get("/professional-summary")
async def get_professional_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_professional_summary(user["user_id"])


@router.delete("/professional-summary")
async def delete_professional_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.delete_professional_summary(user["user_id"])


# ============================================================================
# SKILLS
# ============================================================================

@router.post("/save-skills")
async def save_skills(
    request: Request, 
    skills_payload: SkillSchema, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_skills(skills_payload, user["user_id"])


@router.patch("/update-skills")
async def update_skills(
    request: Request, 
    skills_payload: SkillSchema, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_skills(skills_payload, user["user_id"])


@router.get("/skills")
async def get_skills(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_skills(user["user_id"])


@router.delete("/skills")
async def delete_skills(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.delete_skills(user["user_id"])


# ============================================================================
# EDUCATIONAL INFO
# ============================================================================

@router.post("/save-educational-info")
@router.post("/save-education", include_in_schema=False)
async def save_educational_info(
    request: Request,
    educational_info: EducationalInfoSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_educational_info(educational_info, user["user_id"])


@router.patch("/update-educational-info")
@router.patch("/update-education", include_in_schema=False)
async def update_educational_info(
    request: Request,
    educational_info: EducationalInfoSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_educational_info(educational_info, user["user_id"])


@router.get("/educational-info")
@router.get("/education", include_in_schema=False)
async def get_educational_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_educational_info(user["user_id"])


@router.delete("/educational-info")
@router.delete("/education", include_in_schema=False)
async def delete_educational_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.delete_educational_info(user["user_id"])


# ============================================================================
# WORK EXPERIENCE
# ============================================================================

@router.post("/save-work-experience")
async def save_work_experience(
    request: Request,
    work_experience: WorkExperienceSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_work_experience(work_experience, user["user_id"])


@router.patch("/update-work-experience")
async def update_work_experience(
    request: Request,
    work_experience: WorkExperienceSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_work_experience(work_experience, user["user_id"])


@router.get("/work-experience")
async def get_work_experience(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_work_experience(user["user_id"])


@router.delete("/work-experience")
async def delete_work_experience(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.delete_work_experience(user["user_id"])


# ============================================================================
# PROJECTS INFO
# ============================================================================

@router.post("/save-projects-info")
@router.post("/save-project-info", include_in_schema=False)
async def save_projects_info(
    request: Request,
    projects_payload: ProjectsInfoSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_projects_info(projects_payload, user["user_id"])


@router.patch("/update-projects-info")
@router.patch("/update-project-info", include_in_schema=False)
async def update_projects_info(
    request: Request,
    projects_payload: ProjectsInfoSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_projects_info(projects_payload, user["user_id"])


@router.get("/projects-info")
@router.get("/project-info", include_in_schema=False)
async def get_projects_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_projects_info(user["user_id"])


@router.delete("/projects-info")
@router.delete("/project-info", include_in_schema=False)
async def delete_projects_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.delete_projects_info(user["user_id"])


# ============================================================================
# FULL RESUME DETAILS
# ============================================================================

@router.get("/details")
@router.get("", include_in_schema=False)
async def get_full_resume(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    resume_service = ResumeService(request, db)
    return await resume_service.get_full_resume(user["user_id"])