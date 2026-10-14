from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Request, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ServerException
from app.core.logger import get_logger
from app.core.message import ErrorMessage
from app.core.response import success_response
from app.db.models.job_description import JobDescription
from app.repository.educational_info_resume_repository import EducationalInfoResumeRepository
from app.repository.job_description_repository import JobDescriptionRepository
from app.repository.personal_info_resume_repository import PersonalInfoResumeRepository
from app.repository.professional_summary_resume_repository import ProfessionalSummaryResumeRepository
from app.repository.project_info_resume_repository import ProjectInfoResumeRepository
from app.repository.skill_resume_repository import SkillResumeRepository
from app.repository.user_repository import UserRepository
from app.repository.work_experience_resume_repository import WorkExperienceResumeRepository
from app.schema.job_description import (
    ExperienceSeniorityAnalysis,
    JobDescriptionAnalyzeRequest,
    JobDescriptionListItemResponse,
    JobDescriptionResponse,
    SkillsAnalysisResponse,
    TailoredResumeResponse,
)
from app.services.gemini_service import gemini_service
from app.services.resume_service import ResumeServiceUtils

logger = get_logger(__name__)


class JobDescriptionService:
    def __init__(self, request: Request, db: AsyncSession):
        self.request = request
        self.db = db
        self.user_repo = UserRepository(db)
        self.jd_repo = JobDescriptionRepository(db)
        self.summary_repo = ProfessionalSummaryResumeRepository(db)
        self.skill_repo = SkillResumeRepository(db)
        self.personal_info_repo = PersonalInfoResumeRepository(db)
        self.educational_repo = EducationalInfoResumeRepository(db)
        self.work_exp_repo = WorkExperienceResumeRepository(db)
        self.project_repo = ProjectInfoResumeRepository(db)

        self.resume_service_utils = ResumeServiceUtils(
            self.user_repo,
            self.personal_info_repo,
            self.summary_repo,
            self.skill_repo,
            self.educational_repo,
            self.work_exp_repo,
            self.project_repo,
        )

    async def analyze_job_description(self, user_id: str, payload: JobDescriptionAnalyzeRequest):
        try:
            # 1. Verify user exists
            await self.resume_service_utils.check_user_exist(user_id)

            # 2. Gather candidate's original resume details
            _, summary_obj = await self.resume_service_utils.check_professional_original_summary_exist(user_id)
            _, skills_obj = await self.resume_service_utils.check_skills_exist(user_id)
            _, work_obj = await self.resume_service_utils.check_work_experience_exist(user_id)
            _, proj_obj = await self.resume_service_utils.check_projects_info_exist(user_id)
            _, edu_obj = await self.resume_service_utils.check_educational_info_exist(user_id)

            current_profile: Dict[str, Any] = {
                "professional_summary": summary_obj.summary if summary_obj else "",
                "skills": skills_obj.skills if skills_obj else [],
                "work_experience": work_obj.work_experience if work_obj else [],
                "projects_info": proj_obj.projects if proj_obj else [],
                "educational_info": edu_obj.educations if edu_obj else [],
            }

            # 3. Analyze JD and generate tailored content + interview prep via Gemini
            analysis = await gemini_service.analyze_jd_and_tailor_resume(
                jd_text=payload.job_description,
                current_resume=current_profile,
                job_title=payload.job_title,
                company_name=payload.company_name,
            )

            # 4. Save tailored summary to professional_summary_resume with is_original=False
            tailored_summary_obj = None
            if analysis.get("tailored_summary"):
                tailored_summary_obj = await self.summary_repo.create({
                    "summary": analysis["tailored_summary"],
                    "user_id": user_id,
                    "is_original": False,
                })

            # 5. Save tailored skills to skills_resume with is_original=False
            tailored_skills_obj = None
            if analysis.get("tailored_skills"):
                tailored_skills_obj = await self.skill_repo.create({
                    "skills": analysis["tailored_skills"],
                    "user_id": user_id,
                    "is_original": False,
                })

            # 6. Save complete JobDescription record
            jd_record_data = {
                "job_title": analysis.get("job_title"),
                "company_name": analysis.get("company_name"),
                "job_description": payload.job_description,
                "match_score": analysis.get("match_score", 0),
                "match_rationale": analysis.get("match_rationale"),
                "jd_experience_years": analysis.get("jd_experience_years"),
                "candidate_experience_years": analysis.get("candidate_experience_years"),
                "seniority_level_jd": analysis.get("seniority_level_jd"),
                "seniority_level_candidate": analysis.get("seniority_level_candidate"),
                "experience_gap_verdict": analysis.get("experience_gap_verdict"),
                "extracted_jd_skills": analysis.get("extracted_jd_skills", []),
                "matching_skills": analysis.get("matching_skills", []),
                "missing_skills": analysis.get("missing_skills", []),
                "interview_preparation_tips": analysis.get("interview_preparation_tips", []),
                "tailored_summary": analysis.get("tailored_summary"),
                "tailored_skills": analysis.get("tailored_skills", []),
                "user_id": user_id,
                "professional_summary_id": tailored_summary_obj.id if tailored_summary_obj else None,
                "skill_id": tailored_skills_obj.id if tailored_skills_obj else None,
            }
            jd_obj = await self.jd_repo.create(jd_record_data)

            # 7. Build structured response
            response_data = self._format_jd_response(jd_obj)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Job description analyzed and tailored resume generated successfully",
                data=response_data,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing job description for user {user_id}: {e}", exc_info=True)
            raise ServerException(message=str(e))

    async def get_analysis(self, user_id: str, jd_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)
            jd_obj = await self.jd_repo.get(jd_id)
            if not jd_obj or jd_obj.user_id != user_id:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Job description analysis record not found",
                )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Job description analysis fetched successfully",
                data=self._format_jd_response(jd_obj),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def list_analyses(self, user_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)
            records = await self.jd_repo.get_all(filters={"user_id": user_id})
            items = []
            for r in records:
                items.append({
                    "id": r.id,
                    "job_title": r.job_title,
                    "company_name": r.company_name,
                    "match_score": r.match_score,
                    "seniority_level_jd": r.seniority_level_jd,
                    "seniority_level_candidate": r.seniority_level_candidate,
                    "missing_skills_count": len(r.missing_skills or []),
                    "created_at": r.created_at,
                })

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Job description analyses list fetched successfully",
                data=items,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def delete_analysis(self, user_id: str, jd_id: str):
        try:
            await self.resume_service_utils.check_user_exist(user_id)
            jd_obj = await self.jd_repo.get(jd_id)
            if not jd_obj or jd_obj.user_id != user_id:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Job description analysis record not found",
                )

            # Cleanup linked tailored non-original records
            if jd_obj.professional_summary_id:
                try:
                    await self.summary_repo.delete(jd_obj.professional_summary_id)
                except Exception:
                    pass
            if jd_obj.skill_id:
                try:
                    await self.skill_repo.delete(jd_obj.skill_id)
                except Exception:
                    pass

            await self.jd_repo.delete(jd_id)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Job description analysis deleted successfully",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    def _format_jd_response(self, jd: JobDescription) -> Dict[str, Any]:
        """Formats a JobDescription model instance into a standardized response dictionary."""
        extracted = jd.extracted_jd_skills or []
        matching = jd.matching_skills or []
        missing = jd.missing_skills or []

        return {
            "id": jd.id,
            "job_title": jd.job_title,
            "company_name": jd.company_name,
            "match_score": jd.match_score,
            "match_rationale": jd.match_rationale,
            "experience_analysis": {
                "jd_experience_years": jd.jd_experience_years,
                "candidate_experience_years": jd.candidate_experience_years,
                "seniority_level_jd": jd.seniority_level_jd,
                "seniority_level_candidate": jd.seniority_level_candidate,
                "experience_gap_verdict": jd.experience_gap_verdict,
            },
            "skills_analysis": {
                "total_jd_skills_count": len(extracted),
                "matching_skills_count": len(matching),
                "missing_skills_count": len(missing),
                "extracted_jd_skills": extracted,
                "matching_skills": matching,
                "missing_skills": missing,
            },
            "interview_preparation": jd.interview_preparation_tips or [],
            "tailored_resume": {
                "tailored_summary": jd.tailored_summary,
                "tailored_skills": jd.tailored_skills or [],
                "professional_summary_id": jd.professional_summary_id,
                "skill_id": jd.skill_id,
            },
            "created_at": jd.created_at,
            "updated_at": jd.updated_at,
        }
