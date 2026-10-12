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
async def upload_resume(request:Request, file: UploadFile = File(...), db: Session = Depends(get_db), user = Depends(current_user)):
    resume_service = ResumeService(request, db)
    return await resume_service.upload_resume(user["user_id"], file)