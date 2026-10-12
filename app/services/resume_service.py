from fastapi import UploadFile
from app.repository import base_repository
from fastapi import HTTPException, Request, status as http_status
from sqlalchemy.orm import Session

from app.common.utils import generate_otp, get_unix_time, send_email_verification_email
from app.core.constants import (
    RESUME_FILE_SIZE
)
from app.core.enums import LoginType
from app.core.exception import ServerException
from app.core.logger import get_logger
from app.core.message import ErrorMessage, SuccessMessage
from app.core.response import success_response
from app.db.models.user import User
from app.repository.role_repository import RoleRepository
from app.repository.user_repository import UserRepository
from app.repository.user_session_repository import UserSessionRepository
from app.core.hash import verify_password
from app.core.jwt import generate_token, verify_token

logger = get_logger(__name__)


class ResumeService:
    def __init__(self, request: Request, db: Session):
        self.request = request
        self.db = db
        self.user_repository = UserRepository(db)

    async def upload_resume(self, user_id: int, file: UploadFile):
        try:
            user = self.user_repository.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            
            # Check File Size
            if file.size / 1000 > RESUME_FILE_SIZE:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"File size should be less than {RESUME_FILE_SIZE}MB",
                )
            
            # Check File Type
            if file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="File type should be PDF",
                )
            
            # Save File
            file_name = file.filename
            file_path = f"D:/Vraj Development/Projects/01_project/resume/{user_id + file_name}"
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            
            print(f"file :: {file}")
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))