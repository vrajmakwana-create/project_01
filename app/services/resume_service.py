import re
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, Request, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import RESUME_FILE_SIZE, ONBOARDING_STEPS
from app.core.exception import ServerException
from app.core.logger import get_logger
from app.core.message import ErrorMessage, SuccessMessage
from app.core.response import success_response
from app.repository.user_repository import UserRepository
from app.schema.resume import (
    PersonalInfoSchema,
    PersonalInfoUpdateSchema,
    ProfessionalSummarySchema,
    SkillSchema,
    EducationalInfoSchema,
    WorkExperienceSchema,
    ProjectsInfoSchema,
)
from app.repository.personal_info_resume_repository import PersonalInfoResumeRepository
from app.repository.professional_summary_resume_repository import ProfessionalSummaryResumeRepository
from app.repository.educational_info_resume_repository import EducationalInfoResumeRepository
from app.repository.skill_resume_repository import SkillResumeRepository
from app.repository.project_info_resume_repository import ProjectInfoResumeRepository
from app.repository.work_experience_resume_repository import WorkExperienceResumeRepository
from app.services.gemini_service import gemini_service
from app.services.cloudinary_service import cloudinary_service

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
            self.skill_resume_repo,
            self.educational_info_resume_repo,
            self.work_experience_resume_repo,
            self.project_info_resume_repo,
        )

    # ------------------ Upload ------------------
    async def upload_resume(self, user_id: str, file: UploadFile):
        try:
            # Check user existence
            user = await self.resume_service_utils.check_user_exist(user_id)
            
            # Ensure user cannot upload again if a resume is already uploaded
            if getattr(user, "resume_url", None):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.RESUME_ALREADY_UPLOADED,
                )

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
            
            raw_name = Path(file.filename or "resume.pdf").name
            safe_name = re.sub(r"[^\w\-.]", "_", raw_name)
            unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{safe_name}"

            # Upload resume to Cloudinary (with fallback to local storage if not configured)
            resume_url = cloudinary_service.upload_resume(content, safe_name, user_id)

            # Store resume URL to users table
            await self.user_repository.update(user, {"resume_url": resume_url})

            # Extract all structured resume information using Google Gemini AI
            extracted = await gemini_service.extract_resume_from_pdf(content)

            # Persist extracted data to DB tables
            # await self._persist_extracted_resume(user_id, extracted)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Resume uploaded and information extracted successfully",
                data={
                    "filename": unique_filename,
                    "resume_url": resume_url,
                    "file_path": resume_url,
                    "size_bytes": len(content),
                    "extracted_data": extracted,
                },
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def _persist_extracted_resume(self, user_id: str, extracted: dict):
        """Persists or updates extracted resume information into respective database tables."""
        try:
            # 1. Personal Info
            p_data = extracted.get("personal_info")
            if p_data and (p_data.get("first_name") or p_data.get("email")):
                p_payload = {
                    "first_name": str(p_data.get("first_name") or ""),
                    "last_name": str(p_data.get("last_name") or ""),
                    "email": str(p_data.get("email") or ""),
                    "phone": str(p_data.get("phone") or ""),
                    "address": str(p_data.get("address") or ""),
                    "city": str(p_data.get("city") or ""),
                    "state": str(p_data.get("state") or ""),
                    "zip_code": str(p_data.get("zip_code") or ""),
                    "country": str(p_data.get("country") or ""),
                    "website": str(p_data.get("website") or ""),
                    "github": str(p_data.get("github") or ""),
                    "linkedin": str(p_data.get("linkedin") or ""),
                    "user_id": user_id,
                }
                is_exist, record = await self.resume_service_utils.check_personal_info_exist(user_id)
                if is_exist and record:
                    await self.personal_info_resume_repo.update(record, p_payload)
                else:
                    await self.personal_info_resume_repo.create(p_payload)

            # 2. Professional Summary
            s_data = extracted.get("professional_summary")
            if s_data and s_data.get("summary"):
                is_exist, record = await self.resume_service_utils.check_professional_original_summary_exist(user_id)
                if is_exist and record:
                    await self.professional_summary_resume_repo.update(record, {"summary": s_data["summary"]})
                else:
                    await self.professional_summary_resume_repo.create({
                        "summary": s_data["summary"],
                        "user_id": user_id,
                        "is_original": True,
                    })

            # 3. Skills
            sk_data = extracted.get("skills")
            if sk_data and sk_data.get("skills"):
                is_exist, record = await self.resume_service_utils.check_skills_exist(user_id)
                if is_exist and record:
                    await self.skill_resume_repo.update(record, {"skills": sk_data["skills"]})
                else:
                    await self.skill_resume_repo.create({
                        "skills": sk_data["skills"],
                        "user_id": user_id,
                        "is_original": True,
                    })

            # 4. Educational Info
            edu_data = extracted.get("educational_info")
            if edu_data and edu_data.get("educations"):
                is_exist, record = await self.resume_service_utils.check_educational_info_exist(user_id)
                if is_exist and record:
                    await self.educational_info_resume_repo.update(record, {"educations": edu_data["educations"]})
                else:
                    await self.educational_info_resume_repo.create({
                        "educations": edu_data["educations"],
                        "user_id": user_id,
                    })

            # 5. Work Experience
            work_data = extracted.get("work_experience")
            if work_data and work_data.get("work_experience"):
                is_exist, record = await self.resume_service_utils.check_work_experience_exist(user_id)
                if is_exist and record:
                    await self.work_experience_resume_repo.update(record, {"work_experience": work_data["work_experience"]})
                else:
                    await self.work_experience_resume_repo.create({
                        "work_experience": work_data["work_experience"],
                        "user_id": user_id,
                    })

            # 6. Projects Info
            proj_data = extracted.get("projects_info")
            if proj_data and proj_data.get("projects"):
                is_exist, record = await self.resume_service_utils.check_projects_info_exist(user_id)
                if is_exist and record:
                    await self.project_info_resume_repo.update(record, {"projects": proj_data["projects"]})
                else:
                    await self.project_info_resume_repo.create({
                        "projects": proj_data["projects"],
                        "user_id": user_id,
                        "is_original": True,
                    })
        except Exception as e:
            logger.warning(f"Error persisting extracted resume data for user {user_id}: {e}")

    # ------------------ Personal Info ------------------
    async def save_personal_info(self, personal_info: PersonalInfoSchema, user_id: str):
        try:
            user = await self.resume_service_utils.check_user_exist(user_id)

            # Check User Information already exists
            is_personal_info_exist, _ = await self.resume_service_utils.check_personal_info_exist(user_id)

            if is_personal_info_exist:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.PERSONAL_INFO_ALREADY_EXISTS,
                )

            # Dump Pydantic to Dict
            personal_info_data = personal_info.model_dump()
            personal_info_data["user_id"] = user_id

            # Create DB Record asynchronously
            personal_info_obj = await self.personal_info_resume_repo.create(
                personal_info_data
            )

            # Save Onboarding Step
            await self.user_repository.update(user, {"step_count": ONBOARDING_STEPS["personal_info"]})
        
            return success_response(
                status_code=http_status.HTTP_200_OK,    
                msg=SuccessMessage.PERSONAL_INFORMATION_SAVED_SUCCESSFULLY,
                data=PersonalInfoSchema.model_validate(personal_info_obj),
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def update_personal_info(self, personal_info: PersonalInfoUpdateSchema, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_personal_info_exist, personal_info_data = await self.resume_service_utils.check_personal_info_exist(user_id)

            if not is_personal_info_exist or not personal_info_data:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PERSONAL_INFO__NOT_FOUND,
                )

            new_personal_info_data = personal_info.model_dump(exclude_none=True)

            result = await self.personal_info_resume_repo.update(
                personal_info_data, new_personal_info_data
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PERSONAL_INFORMATION_UPDATED_SUCCESSFULLY,
                data=PersonalInfoSchema.model_validate(result),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def get_personal_info(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_personal_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PERSONAL_INFO__NOT_FOUND,
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY,
                data=PersonalInfoSchema.model_validate(record),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_personal_info(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_personal_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PERSONAL_INFO__NOT_FOUND,
                )

            await self.personal_info_resume_repo.delete(record.id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PERSONAL_INFORMATION_DELETED_SUCCESSFULLY,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    # ------------------ Professional Summary ------------------
    async def save_professional_summary(self, professional_summary: ProfessionalSummarySchema, user_id: str):
        try:
            user = await self.resume_service_utils.check_user_exist(user_id)

            is_professional_summary_exist, _ = await self.resume_service_utils.check_professional_original_summary_exist(
                user_id
            )

            if is_professional_summary_exist:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.PROFESSIONAL_SUMMARY_ALREADY_EXIST,
                )

            professional_summary_data = professional_summary.model_dump()
            professional_summary_data.update(
                {
                    "user_id": user_id,
                    "is_original": True,
                }
            )

            result = await self.professional_summary_resume_repo.create(
                professional_summary_data
            )

            # Save Onboarding Step
            await self.user_repository.update(user, {"step_count": ONBOARDING_STEPS["professional_summary"]})

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PROFESSIONAL_SUMMARY_SAVED_SUCCESSFULLY,
                data=ProfessionalSummarySchema.model_validate(result),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def update_professional_summary(self, professional_summary: ProfessionalSummarySchema, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_professional_summary_exist, summary_data = await self.resume_service_utils.check_professional_original_summary_exist(
                user_id
            )

            if not is_professional_summary_exist or summary_data is None:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PROFESSIONAL_SUMMARY_NOT_FOUND,
                )

            result = await self.professional_summary_resume_repo.update(
                summary_data, {"summary": professional_summary.summary}
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PROFESSIONAL_SUMMARY_UPDATED_SUCCESSFULLY,
                data=ProfessionalSummarySchema.model_validate(result),
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def get_professional_summary(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_professional_original_summary_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PROFESSIONAL_SUMMARY_NOT_FOUND,
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY,
                data=ProfessionalSummarySchema.model_validate(record),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_professional_summary(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_professional_original_summary_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PROFESSIONAL_SUMMARY_NOT_FOUND,
                )

            await self.professional_summary_resume_repo.delete(record.id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PROFESSIONAL_SUMMARY_DELETED_SUCCESSFULLY,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    # ------------------ Skills ------------------
    async def save_skills(self, skills_payload: SkillSchema, user_id: str):
        try:
            user = await self.resume_service_utils.check_user_exist(user_id)

            is_skill_exist, _ = await self.resume_service_utils.check_skills_exist(user_id)

            if is_skill_exist:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.SKILLS_ALREADY_EXISTS,
                )

            skill_data = skills_payload.model_dump()
            skill_data.update(
                {
                    "is_original": True, 
                    "user_id": user_id,
                }
            )

            result = await self.skill_resume_repo.create(
                skill_data
            )

            # Save Onboarding Step
            await self.user_repository.update(user, {"step_count": ONBOARDING_STEPS["skills"]})

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.SKILLS_SAVED_SUCCESSFULLY,
                data=SkillSchema.model_validate(result),
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))
            
    async def update_skills(self, skills_payload: SkillSchema, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_skill_exist, skills_record = await self.resume_service_utils.check_skills_exist(user_id)

            if not is_skill_exist or not skills_record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.SKILLS_NOT_FOUND,
                )

            skill_data = skills_payload.model_dump()

            result = await self.skill_resume_repo.update(
                skills_record, {"skills": skill_data.get("skills", [])}
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.SKILLS_UPDATED_SUCCESSFULLY,
                data=SkillSchema.model_validate(result),
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def get_skills(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_skills_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.SKILLS_NOT_FOUND,
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY,
                data=SkillSchema.model_validate(record),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_skills(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_skills_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.SKILLS_NOT_FOUND,
                )

            await self.skill_resume_repo.delete(record.id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.SKILLS_DELETED_SUCCESSFULLY,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    # ------------------ Educational Info ------------------
    async def save_educational_info(self, educational_info: EducationalInfoSchema, user_id: str):
        try:
            user = await self.resume_service_utils.check_user_exist(user_id)

            is_exist, _ = await self.resume_service_utils.check_educational_info_exist(user_id)
            if is_exist:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.EDUCATIONAL_INFO_ALREADY_EXISTS,
                )

            data = educational_info.model_dump()
            data["user_id"] = user_id

            result = await self.educational_info_resume_repo.create(data)

            # Save Onboarding Step
            await self.user_repository.update(user, {"step_count": ONBOARDING_STEPS["educational_info"]})

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.EDUCATIONAL_INFO_SAVED_SUCCESSFULLY,
                data=EducationalInfoSchema.model_validate(result),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def update_educational_info(self, educational_info: EducationalInfoSchema, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_educational_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.EDUCATIONAL_INFO_NOT_FOUND,
                )

            data = educational_info.model_dump()
            result = await self.educational_info_resume_repo.update(
                record, {"educations": data.get("educations", [])}
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.EDUCATIONAL_INFO_UPDATED_SUCCESSFULLY,
                data=EducationalInfoSchema.model_validate(result),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def get_educational_info(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_educational_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.EDUCATIONAL_INFO_NOT_FOUND,
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY,
                data=EducationalInfoSchema.model_validate(record),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_educational_info(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_educational_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.EDUCATIONAL_INFO_NOT_FOUND,
                )

            await self.educational_info_resume_repo.delete(record.id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.EDUCATIONAL_INFO_DELETED_SUCCESSFULLY,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    # ------------------ Work Experience ------------------
    async def save_work_experience(self, work_experience: WorkExperienceSchema, user_id: str):
        try:
            user = await self.resume_service_utils.check_user_exist(user_id)

            is_exist, _ = await self.resume_service_utils.check_work_experience_exist(user_id)
            if is_exist:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.WORK_EXPERIENCE_ALREADY_EXISTS,
                )

            data = work_experience.model_dump()
            data["user_id"] = user_id

            result = await self.work_experience_resume_repo.create(data)

            # Save Onboarding Step
            await self.user_repository.update(user, {"step_count": ONBOARDING_STEPS["work_experience"]})

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.WORK_EXPERIENCE_SAVED_SUCCESSFULLY,
                data=WorkExperienceSchema.model_validate(result),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def update_work_experience(self, work_experience: WorkExperienceSchema, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_work_experience_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.WORK_EXPERIENCE_NOT_FOUND,
                )

            data = work_experience.model_dump()
            result = await self.work_experience_resume_repo.update(
                record, {"work_experience": data.get("work_experience", [])}
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.WORK_EXPERIENCE_UPDATED_SUCCESSFULLY,
                data=WorkExperienceSchema.model_validate(result),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def get_work_experience(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_work_experience_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.WORK_EXPERIENCE_NOT_FOUND,
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY,
                data=WorkExperienceSchema.model_validate(record),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_work_experience(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_work_experience_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.WORK_EXPERIENCE_NOT_FOUND,
                )

            await self.work_experience_resume_repo.delete(record.id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.WORK_EXPERIENCE_DELETED_SUCCESSFULLY,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    # ------------------ Projects Info ------------------
    async def save_projects_info(self, projects_payload: ProjectsInfoSchema, user_id: str):
        try:
            user = await self.resume_service_utils.check_user_exist(user_id)

            is_exist, _ = await self.resume_service_utils.check_projects_info_exist(user_id)
            if is_exist:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.PROJECTS_INFO_ALREADY_EXISTS,
                )

            data = projects_payload.model_dump()
            data.update(
                {
                    "is_original": True,
                    "user_id": user_id,
                }
            )

            result = await self.project_info_resume_repo.create(data)

            # Save Final Onboarding Step and Complete Onboarding
            await self.user_repository.update(user, {"step_count": ONBOARDING_STEPS["projects"], "onboarding_completed": True})
            

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PROJECTS_INFO_SAVED_SUCCESSFULLY,
                data=ProjectsInfoSchema.model_validate(result),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def update_projects_info(self, projects_payload: ProjectsInfoSchema, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_projects_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PROJECTS_INFO_NOT_FOUND,
                )

            data = projects_payload.model_dump()
            result = await self.project_info_resume_repo.update(
                record, {"projects": data.get("projects", [])}
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PROJECTS_INFO_UPDATED_SUCCESSFULLY,
                data=ProjectsInfoSchema.model_validate(result),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def get_projects_info(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_projects_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PROJECTS_INFO_NOT_FOUND,
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY,
                data=ProjectsInfoSchema.model_validate(record),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_projects_info(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            is_exist, record = await self.resume_service_utils.check_projects_info_exist(user_id)
            if not is_exist or not record:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.PROJECTS_INFO_NOT_FOUND,
                )

            await self.project_info_resume_repo.delete(record.id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.PROJECTS_INFO_DELETED_SUCCESSFULLY,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    # ------------------ Full Resume ------------------
    async def get_full_resume(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)

            _, personal_info = await self.resume_service_utils.check_personal_info_exist(user_id)
            _, summary = await self.resume_service_utils.check_professional_original_summary_exist(user_id)
            _, skills = await self.resume_service_utils.check_skills_exist(user_id)
            _, education = await self.resume_service_utils.check_educational_info_exist(user_id)
            _, work_exp = await self.resume_service_utils.check_work_experience_exist(user_id)
            _, projects = await self.resume_service_utils.check_projects_info_exist(user_id)

            data = {
                "personal_info": PersonalInfoSchema.model_validate(personal_info).model_dump() if personal_info else None,
                "professional_summary": ProfessionalSummarySchema.model_validate(summary).model_dump() if summary else None,
                "skills": SkillSchema.model_validate(skills).model_dump() if skills else None,
                "educational_info": EducationalInfoSchema.model_validate(education).model_dump() if education else None,
                "work_experience": WorkExperienceSchema.model_validate(work_exp).model_dump() if work_exp else None,
                "projects_info": ProjectsInfoSchema.model_validate(projects).model_dump() if projects else None,
            }

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.RESUME_FETCHED_SUCCESSFULLY,
                data=data,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))


class ResumeServiceUtils:

    def __init__(
        self, 
        user_repository: UserRepository, 
        personal_info_repo: PersonalInfoResumeRepository, 
        professional_summary_resume_repo: ProfessionalSummaryResumeRepository,
        skills_repo: SkillResumeRepository,
        educational_info_repo: EducationalInfoResumeRepository,
        work_experience_repo: WorkExperienceResumeRepository,
        project_info_repo: ProjectInfoResumeRepository,
    ):
        self.user_repository = user_repository
        self.personal_info_repo = personal_info_repo
        self.professional_summary_repo = professional_summary_resume_repo
        self.skills_repo = skills_repo
        self.educational_info_repo = educational_info_repo
        self.work_experience_repo = work_experience_repo
        self.project_info_repo = project_info_repo

    # Utils Methods
    async def check_user_exist(self, user_id: str):
        user = await self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=ErrorMessage.USER_NOT_FOUND,
            )
        return user
    
    async def check_personal_info_exist(self, user_id: str):
        is_exist = await self.personal_info_repo.get_by_field(
            "user_id", user_id,
        )

        if is_exist:
            return True, is_exist
        return False, None

    async def check_professional_original_summary_exist(self, user_id: str):
        is_exist = await self.professional_summary_repo.get_all(
            filters={ 
                "user_id": user_id,
                "is_original": True
            }
        )

        if is_exist:
            return True, is_exist[0]
        return False, None
    
    async def check_skills_exist(self, user_id: str):
        skills = await self.skills_repo.get_all(
            filters={
                "user_id": user_id,
                "is_original": True
            }
        )

        if skills:
            return True, skills[0]
        return False, None

    async def check_educational_info_exist(self, user_id: str):
        educations = await self.educational_info_repo.get_all(
            filters={"user_id": user_id}
        )
        if educations:
            return True, educations[0]
        return False, None

    async def check_work_experience_exist(self, user_id: str):
        work_exp = await self.work_experience_repo.get_all(
            filters={"user_id": user_id}
        )
        if work_exp:
            return True, work_exp[0]
        return False, None

    async def check_projects_info_exist(self, user_id: str):
        projects = await self.project_info_repo.get_all(
            filters={
                "user_id": user_id,
                "is_original": True,
            }
        )
        if projects:
            return True, projects[0]
        all_proj = await self.project_info_repo.get_all(filters={"user_id": user_id})
        if all_proj:
            return True, all_proj[0]
        return False, None