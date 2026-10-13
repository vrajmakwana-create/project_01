from app.schema.resume import SkillSchema
from app.schema.resume import PersonalInfoSchema, ProfessionalSummarySchema, PersonalInfoUpdateSchema
from app.core.dependecy import PermissionCheck
from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependecy import RoleCheck, current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schema.user import UserLogin, UserOtpVerify, UserRegistration, UserChangePassword, UserRefreshToken
from app.services.resume_service import ResumeService
from app.core.constants import Roles

router = APIRouter(prefix="/resume", tags=["Resume"])

@router.post("/upload")
async def upload_resume(
    request:Request, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.upload_resume(user["user_id"], file)

@router.post("/save-personal-info")
async def save_personal_info(request:Request, 
    personal_info: PersonalInfoSchema, 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_personal_info(personal_info, user['user_id'])

@router.patch("/update-personal-info")
async def update_personal_info(request:Request, 
    personal_info: PersonalInfoUpdateSchema, 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_personal_info(personal_info, user['user_id'])

@router.post("/save-professional-summary")
async def save_professional_summary(request:Request, 
    personal_summary: ProfessionalSummarySchema, 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_professional_summary(personal_summary, user['user_id'])

@router.patch("/update-professional-summary")
async def save_professional_summary(request:Request, 
    personal_summary: ProfessionalSummarySchema, 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_professional_summary(personal_summary, user['user_id'])

@router.post("/save-skills")
async def save_skills(request:Request, 
    skills_payload: SkillSchema, 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.save_skills(skills_payload, user['user_id'])

@router.patch("/update-skills")
async def update_skills(request:Request, 
    skills_payload: SkillSchema, 
    db: Session = Depends(get_db), 
    user = Depends(current_user)
):
    resume_service = ResumeService(request, db)
    return await resume_service.update_skills(skills_payload, user['user_id'])