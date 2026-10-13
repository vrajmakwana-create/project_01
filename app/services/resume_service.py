import re
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, Request, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import RESUME_FILE_SIZE
from app.core.exception import ServerException
from app.core.logger import get_logger
from app.core.message import ErrorMessage, SuccessMessage
from app.core.response import success_response
from app.repository.user_repository import UserRepository
from app.schema.resume import PersonalInfoSchema, ProfessionalSummarySchema, SkillSchema
from app.repository.personal_info_resume_repository import PersonalInfoResumeRepository
from app.repository.professional_summary_resume_repository import ProfessionalSummaryResumeRepository
from app.repository.educational_info_resume_repository import EducationalInfoResumeRepository
from app.repository.skill_resume_repository import SkillResumeRepository
from app.repository.project_info_resume_repository import ProjectInfoResumeRepository
from app.repository.work_experience_resume_repository import WorkExperienceResumeRepository

logger = get_logger(__name__)


class ResumeService:
    def __init__(self, request: Request, db: AsyncSession):
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

    async def upload_resume(self, user_id: str, file: UploadFile):
        try:
            # Check user existence
            await self.resume_service_utils.check_user_exist(user_id)
            
            # Read file content asynchronously
            content = await file.read()

            # Check File Size (RESUME_FILE_SIZE in MB)
            max_size_bytes = RESUME_FILE_SIZE * 1024 * 1024
            if len(content) > max_size_bytes:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"File size should be less than {RESUME_FILE_SIZE}MB",
                )
            
            # Check File Type
            is_pdf = (file.content_type == "application/pdf") or (
                bool(file.filename and file.filename.lower().endswith(".pdf"))
            )
            if not is_pdf:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="File type should be PDF",
                )
            
            # Save file safely to project uploads directory
            upload_dir = Path("uploads/resumes")
            upload_dir.mkdir(parents=True, exist_ok=True)

            raw_name = Path(file.filename or "resume.pdf").name
            safe_name = re.sub(r"[^\w\-.]", "_", raw_name)
            unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
            target_path = upload_dir / unique_filename

            target_path.write_bytes(content)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Resume uploaded successfully",
                data={
                    "filename": unique_filename,
                    "file_path": str(target_path).replace("\\", "/"),
                    "size_bytes": len(content),
                },
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))
    
    async def save_personal_info(self, personal_info, user_id: str):
        try:
            # Check User Information already exists
            is_personal_info_exist, _ = await self.resume_service_utils.check_personal_info_exist(user_id)

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

            # Create DB Record asynchronously
            personal_info_obj = await self.personal_info_resume_repo.create(
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
            is_personal_info_exist, personal_info_data = await self.resume_service_utils.check_personal_info_exist(user_id)

            if not is_personal_info_exist and not personal_info_data:
                raise HTTPException(
                    status_code = http_status.HTTP_404_NOT_FOUND,
                    detail = ErrorMessage.PERSONAL_INFO__NOT_FOUND
                )

            new_personal_info_data = personal_info.model_dump(exclude_none=True)

            # Update to DB asynchronously
            result = await self.personal_info_resume_repo.update(
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
            # Check user existence
            await self.resume_service_utils.check_user_exist(user_id)

            # Check Professional Summary for user_id
            is_professional_summary_exist, _ = await self.resume_service_utils.check_professional_original_summary_exist(
                user_id
            )

            if is_professional_summary_exist:
                raise HTTPException(
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

            # Record professional summary asynchronously
            result = await self.professional_summary_resume_repo.create(
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
            is_professional_summary_exist, summary_data = await self.resume_service_utils.check_professional_original_summary_exist(
                user_id
            )

            if not is_professional_summary_exist and summary_data is None:
                raise HTTPException(
                    status_code = http_status.HTTP_404_NOT_FOUND,
                    detail = ErrorMessage.PROFESSIONAL_SUMMARY_NOT_FOUND
                )

            result = await self.professional_summary_resume_repo.update(
                summary_data, {"summary": professional_summary.summary}
            )

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.PROFESSIONAL_SUMMARY_UPDATED_SUCCESSFULLY,
                data= ProfessionalSummarySchema.model_validate(result)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message = str(e))

    async def save_skills(self, skills_payload: SkillSchema, user_id: str):
        try:
            is_skill_exist, _ = await self.resume_service_utils.check_skills_exist(user_id)

            if is_skill_exist:
                raise HTTPException(
                    status_code = http_status.HTTP_400_BAD_REQUEST,
                    detail = ErrorMessage.SKILLS_ALREADY_EXISTS
                )

            skill_data = skills_payload.model_dump()

            skill_data.update(
                {
                    "is_original": True, 
                    "user_id": user_id
                }
            )

            result = await self.skill_resume_repo.create(
                skill_data
            )

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.SKILLS_SAVED_SUCCESSFULLY,
                data= SkillSchema.model_validate(result)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message = str(e))
            
    async def update_skills(self, skills_payload: SkillSchema, user_id: str):
        try:
            is_skill_exist, skills_record = await self.resume_service_utils.check_skills_exist(user_id)

            if not is_skill_exist or not skills_record:
                raise HTTPException(
                    status_code = http_status.HTTP_404_NOT_FOUND,
                    detail = ErrorMessage.SKILLS_NOT_FOUND
                )

            skill_data = skills_payload.model_dump()

            # Update the Skill Record Db Object asynchronously
            result = await self.skill_resume_repo.update(
                skills_record, {"skills": skill_data.get("skills", [])}
            )

            return success_response(
                status_code= http_status.HTTP_200_OK,
                msg=SuccessMessage.SKILLS_SAVED_SUCCESSFULLY,
                data= SkillSchema.model_validate(result)
            )
            
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
    async def check_user_exist(self, user_id):
        user = await self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=ErrorMessage.USER_NOT_FOUND,
            )
    
    async def check_personal_info_exist(self, user_id):
        is_exist = await self.personal_info_repo.get_by_field(
            "user_id", user_id,
        )

        if is_exist:
            return True, is_exist
        return False, None

    async def check_professional_original_summary_exist(self, user_id):
        is_exist = await self.professional_summary_repo.get_all(
            filters = { 
                "user_id": user_id,
                "is_original": True
            }
        )

        if is_exist:
            return True, is_exist[0]
        return False, None
    
    async def check_skills_exist(self, user_id):
        skills = await self.skills_repo.get_all(
            filters = {
                "user_id": user_id,
                "is_original": True
            }
        )

        if skills:
            return True, skills[0]
        return False, None