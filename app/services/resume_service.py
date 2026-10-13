from select import select
from app.core import message
from fastapi import UploadFile
from app.repository import base_repository
from fastapi import HTTPException, Request, status as http_status
from sqlalchemy.orm import Session

from app.common.utils import generate_otp, get_unix_time, send_email_verification_email
from app.core.constants import (
    RESUME_FILE_SIZE
)
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
from app.schema.resume import PersonalInfoSchema, ProfessionalSummarySchema
from app.repository.personal_info_resume_repository import PersonalInfoResumeRepository
from app.repository.professional_summary_resume_repository import ProfessionalSummaryResumeRepository
from app.repository.educational_info_resume_repository import EducationalInfoResumeRepository
from app.repository.skill_resume_repository import SkillResumeRepository
from app.repository.project_info_resume_repository import ProjectInfoResumeRepository
from app.repository.work_experience_resume_repository import WorkExperienceResumeRepository


logger = get_logger(__name__)


class ResumeService:
    def __init__(self, request: Request, db: Session):
        self.request = request
        self.db = db
        self.user_repository = UserRepository(db)
        self.personal_info_resume_repo = PersonalInfoResumeRepository(db)
        self.professional_summary_resume_repo = ProfessionalSummaryResumeRepository(db)
        self.skill_resume_repo = SkillResumeRepository(db)
        self.educational_info_resume_repo = EducationalInfoResumeRepository(db)
        self.work_experience_resume_repo = WorkExperienceResumeRepository(db)
        self.project_info_resume_repo = ProjectInfoResumeRepository(db)

        # Resume Service Utils
        self.resume_service_utils = ResumeServiceUtils(
            self.user_repository, 
            self.personal_info_resume_repo,
            self.professional_summary_resume_repo,
            self.skill_resume_repo
        )

    async def upload_resume(self, user_id: int, file: UploadFile):
        try:
            # Check user existance
            self.resume_service_utils.check_user_exist(user_id)
            
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
    
    async def save_personal_info(self, personal_info, user_id: str):
        try:
            # Check User Information already exists
            is_personal_info_exist, _ = self.resume_service_utils.check_personal_info_exist(user_id)

            if is_personal_info_exist:
                raise HTTPException(
                    status_code = http_status.HTTP_400_BAD_REQUEST,
                    detail = ErrorMessage.PERSONAL_INFO_ALREADY_EXISTS
                )

            # Dump Pydantic to Dict
            personal_info_data = personal_info.model_dump()

            # Add user id in personal info
            personal_info_data.update(
                {
                    "user_id": user_id
                }
            )

            # Create DB Record
            personal_info_obj = self.personal_info_resume_repo.create(
                personal_info_data
            )

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.PERSONAL_INFORMATION_SAVED_SUCCESSFULLY,
                data= PersonalInfoSchema.model_validate(personal_info_obj)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def update_personal_info(self, personal_info, user_id: str):
        try:
            is_personal_info_exist, personal_info_data = self.resume_service_utils.check_personal_info_exist(user_id)

            if not is_personal_info_exist and not personal_info_data:
                raise HTTPException(
                    status_code = http_status.HTTP_404_NOT_FOUND,
                    detail = ErrorMessage.PERSONAL_INFO__NOT_FOUND
                )

            new_personal_info_data = personal_info.model_dump(exclude_none=True)

            # Update to DB
            result = self.personal_info_resume_repo.update(
                personal_info_data, new_personal_info_data
            )

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.PERSONAL_INFORMATION_UPDATED_SUCCESSFULLY,
                data= PersonalInfoSchema.model_validate(result)
            )

        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message = str(e))

    async def save_professional_summary(self, professional_summary, user_id: str):
        try:
            # Check user existance
            self.resume_service_utils.check_user_exist(user_id)

            # Check Professional Summary for user_id
            is_professional_summary_exist, _ = self.resume_service_utils.check_professional_original_summary_exist(
                user_id
            )

            if is_professional_summary_exist:
                return HTTPException(
                    status_code = http_status.HTTP_400_BAD_REQUEST,
                    detail = ErrorMessage.PROFESSIONAL_SUMMARY_ALREADY_EXIST
                )

            # dump professional summary
            professional_summary_data = professional_summary.model_dump()

            # Append user_id
            professional_summary_data.update(
                {
                    "user_id": user_id,
                    "is_original": True
                }
            )

            # Record professional summary 
            result = self.professional_summary_resume_repo.create(
                professional_summary_data
            )

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.PROFESSIONAL_SUMMARY_SAVED_SUCCESSFULLY,
                data= ProfessionalSummarySchema.model_validate(result)
            )

        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message = str(e))

    async def update_professional_summary(self, professional_summary, user_id: str):
        try:
            is_professional_summary_exist, summary_data = self.resume_service_utils.check_professional_original_summary_exist(
                user_id
            )

            if not is_professional_summary_exist and summary_data is None:
                raise HTTPException(
                    status_code = http_status.HTTP_404_NOT_FOUND,
                    detail = ErrorMessage.PROFESSIONAL_SUMMARY_NOT_FOUND
                )

            summary_data.summary = professional_summary.summary
            self.professional_summary_resume_repo.db.commit()
            self.professional_summary_resume_repo.db.refresh(summary_data)

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.PROFESSIONAL_SUMMARY_UPDATED_SUCCESSFULLY,
                data= ProfessionalSummarySchema.model_validate(summary_data)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message = str(e))

    
    async def save_skills(self, skills: list[str], user_id: str):
        try:
            pass
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message = str(e))
            

class ResumeServiceUtils:

    def __init__(
        self, 
        user_repository: UserRepository, 
        personal_info_repo: PersonalInfoResumeRepository, 
        professional_summary_resume_repo: ProfessionalSummaryResumeRepository,
        skills_repo: SkillResumeRepository
    ):
        self.user_repository = user_repository
        self.personal_info_repo = personal_info_repo
        self.professional_summary_repo = professional_summary_resume_repo
        self.skills_repo = skills_repo

    # Utils Methods
    def check_user_exist(self, user_id):
        user = self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=ErrorMessage.USER_NOT_FOUND,
            )
    
    def check_personal_info_exist(self, user_id):
        is_exist = self.personal_info_repo.get_by_field(
            "user_id", user_id,
        )

        return True if is_exist else False, is_exist or None

    def check_professional_original_summary_exist(self, user_id):
        is_exist = self.professional_summary_repo.get_all(
            filters = { 
                "user_id": user_id,
                "is_original": True
            }
        )

        return True if len(is_exist) == 1 else False, is_exist[0] or None