import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import Counter

from fastapi import HTTPException, Request, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ServerException
from app.core.logger import get_logger
from app.core.response import success_response
from app.common.utils import (
    calculate_candidate_experience_years,
    structure_skills_into_categories,
)
from app.repository.user_repository import UserRepository
from app.repository.personal_info_resume_repository import PersonalInfoResumeRepository
from app.repository.professional_summary_resume_repository import ProfessionalSummaryResumeRepository
from app.repository.skill_resume_repository import SkillResumeRepository
from app.repository.educational_info_resume_repository import EducationalInfoResumeRepository
from app.repository.work_experience_resume_repository import WorkExperienceResumeRepository
from app.repository.project_info_resume_repository import ProjectInfoResumeRepository
from app.repository.job_description_repository import JobDescriptionRepository
from app.services.resume_service import ResumeServiceUtils
from app.schema.dashboard import (
    DashboardKPIs,
    SectionStatus,
    PrimaryResumeData,
    SkillsAnalytics,
    RecentApplicationItem,
    MatchDistribution,
    TailoredApplicationsAnalytics,
    ActionableRecommendation,
    DashboardResponseData,
)

logger = get_logger(__name__)

ACTION_VERBS = {
    "built", "developed", "designed", "architected", "implemented", "managed",
    "led", "created", "optimized", "deployed", "spearheaded", "engineered",
    "delivered", "maintained", "automated", "improved", "integrated", "scaled",
}


class DashboardService:
    def __init__(self, request: Request, db: AsyncSession):
        self.request = request
        self.db = db
        self.user_repo = UserRepository(db)
        self.personal_info_repo = PersonalInfoResumeRepository(db)
        self.summary_repo = ProfessionalSummaryResumeRepository(db)
        self.skills_repo = SkillResumeRepository(db)
        self.edu_repo = EducationalInfoResumeRepository(db)
        self.work_repo = WorkExperienceResumeRepository(db)
        self.project_repo = ProjectInfoResumeRepository(db)
        self.jd_repo = JobDescriptionRepository(db)

        self.resume_utils = ResumeServiceUtils(
            user_repository=self.user_repo,
            personal_info_repo=self.personal_info_repo,
            professional_summary_resume_repo=self.summary_repo,
            skills_repo=self.skills_repo,
            educational_info_repo=self.edu_repo,
            work_experience_repo=self.work_repo,
            project_info_repo=self.project_repo,
        )

    @staticmethod
    def _format_timestamp(ts: Any) -> Optional[str]:
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            sec = ts / 1000.0 if ts > 1e11 else ts
            return datetime.fromtimestamp(sec, timezone.utc).isoformat()
        if hasattr(ts, "isoformat"):
            return ts.isoformat()
        return str(ts)

    @staticmethod
    def _get_year(ts: Any) -> int:
        if ts is None:
            return datetime.now(timezone.utc).year
        if isinstance(ts, (int, float)):
            sec = ts / 1000.0 if ts > 1e11 else ts
            return datetime.fromtimestamp(sec, timezone.utc).year
        if hasattr(ts, "year"):
            return ts.year
        return datetime.now(timezone.utc).year

    @staticmethod
    def _get_ts_number(item: Any) -> float:
        val = getattr(item, "created_at", None)
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        if hasattr(val, "timestamp"):
            return val.timestamp()
        return 0.0

    async def get_dashboard_analytics(self, user_id: str):
        try:
            # 1. Verify user exists
            user = await self.resume_utils.check_user_exist(user_id)

            # 2. Retrieve resume sections
            has_p, p_obj = await self.resume_utils.check_personal_info_exist(user_id)
            has_s, s_obj = await self.resume_utils.check_professional_original_summary_exist(user_id)
            has_sk, sk_obj = await self.resume_utils.check_skills_exist(user_id)
            has_edu, edu_obj = await self.resume_utils.check_educational_info_exist(user_id)
            has_w, w_obj = await self.resume_utils.check_work_experience_exist(user_id)
            has_pr, pr_obj = await self.resume_utils.check_projects_info_exist(user_id)

            # 3. Retrieve tailored job descriptions
            jds = await self.jd_repo.get_all(filters={"user_id": user_id})

            # Work list & Experience
            work_list = w_obj.work_experience if (has_w and w_obj) else []
            total_exp_years = calculate_candidate_experience_years(work_list)

            # 4. Compute Overall Resume Score & Sub-scores
            resume_score, score_breakdown = self._calculate_overall_resume_score(
                p_obj=p_obj if has_p else None,
                s_obj=s_obj if has_s else None,
                sk_obj=sk_obj if has_sk else None,
                work_list=work_list,
                edu_obj=edu_obj if has_edu else None,
                pr_obj=pr_obj if has_pr else None,
            )

            # 5. Compute ATS Parsing Rate
            ats_rate = self._calculate_ats_parsing_rate(
                has_p=has_p, p_obj=p_obj,
                has_s=has_s, s_obj=s_obj,
                has_sk=has_sk,
                has_w=has_w, work_list=work_list,
                has_edu=has_edu,
                has_pr=has_pr,
            )

            # 6. Target Role & Candidate Info
            target_role = "Candidate Profile"
            if work_list and isinstance(work_list, list) and len(work_list) > 0:
                first_work = work_list[0]
                if isinstance(first_work, dict):
                    target_role = first_work.get("job_title") or first_work.get("title") or target_role

            cand_name = ""
            if has_p and p_obj:
                cand_name = f"{p_obj.first_name or ''} {p_obj.last_name or ''}".strip()
            if not cand_name:
                cand_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Candidate"

            # Determine Year and Last Updated timestamp
            curr_year = self._get_year(getattr(user, "updated_at", None) or getattr(user, "created_at", None))
            last_updated_str = self._format_timestamp(getattr(user, "updated_at", None) or getattr(user, "created_at", None))

            # Completeness
            sections_present = [has_p, has_s, has_sk, has_edu, has_w, has_pr]
            completeness = int((sum(1 for s in sections_present if s) / 6.0) * 100)

            # 7. Skills Analytics
            raw_skills = sk_obj.skills if (has_sk and sk_obj) else {}
            structured_skills = structure_skills_into_categories(raw_skills)
            total_skills_count = sum(len(items) for items in structured_skills.values())
            populated_categories_count = len(structured_skills)

            # Top matching and missing skills from JDs
            all_matching_skills = []
            all_missing_skills = []
            for jd in jds:
                all_matching_skills.extend(jd.matching_skills or [])
                all_missing_skills.extend(jd.missing_skills or [])

            top_matching = [item for item, _ in Counter(all_matching_skills).most_common(5)]
            top_missing = [item for item, _ in Counter(all_missing_skills).most_common(5)]

            # 8. Tailored Applications Analytics
            total_jds = len(jds)
            avg_match = round(sum(j.match_score for j in jds) / total_jds, 1) if total_jds > 0 else 0.0

            high_match = sum(1 for j in jds if j.match_score >= 80)
            mod_match = sum(1 for j in jds if 60 <= j.match_score < 80)
            low_match = sum(1 for j in jds if j.match_score < 60)

            # Sort recent applications
            sorted_jds = sorted(jds, key=self._get_ts_number, reverse=True)[:5]

            recent_apps = []
            for j in sorted_jds:
                created_str = self._format_timestamp(getattr(j, "created_at", None))
                recent_apps.append(
                    RecentApplicationItem(
                        id=str(j.id),
                        job_title=j.job_title,
                        company_name=j.company_name,
                        match_score=j.match_score,
                        seniority_level_jd=j.seniority_level_jd,
                        created_at=created_str,
                        resume_url=j.resume_url,
                    )
                )

            # 9. Dynamic Actionable Recommendations
            recommendations = self._generate_recommendations(
                has_p=has_p, p_obj=p_obj,
                has_s=has_s, s_obj=s_obj,
                has_sk=has_sk, total_skills_count=total_skills_count, populated_cats=populated_categories_count,
                has_w=has_w, work_list=work_list,
                has_pr=has_pr, pr_obj=pr_obj,
                total_jds=total_jds,
                top_missing=top_missing,
            )

            # 10. Build final structured payload
            dashboard_data = DashboardResponseData(
                kpis=DashboardKPIs(
                    overall_resume_score=resume_score,
                    ats_parsing_rate=ats_rate,
                    tailored_applications_count=total_jds,
                    average_match_score=avg_match,
                    total_experience_years=total_exp_years,
                ),
                primary_resume=PrimaryResumeData(
                    target_role=target_role,
                    candidate_name=cand_name,
                    year=curr_year,
                    resume_url=getattr(user, "resume_url", None),
                    last_updated_at=last_updated_str,
                    completeness_score=completeness,
                    sections_status=SectionStatus(
                        personal_info=bool(has_p),
                        professional_summary=bool(has_s),
                        skills=bool(has_sk),
                        work_experience=bool(has_w),
                        projects=bool(has_pr),
                        education=bool(has_edu),
                    ),
                ),
                skills_analytics=SkillsAnalytics(
                    total_skills_count=total_skills_count,
                    populated_categories_count=populated_categories_count,
                    skills_by_category=structured_skills,
                    top_matching_market_skills=top_matching,
                    top_missing_skills_for_interviews=top_missing,
                ),
                tailored_applications_analytics=TailoredApplicationsAnalytics(
                    total_count=total_jds,
                    match_distribution=MatchDistribution(
                        high_match_80_plus=high_match,
                        moderate_match_60_to_79=mod_match,
                        low_match_below_60=low_match,
                    ),
                    recent_tailored_applications=recent_apps,
                ),
                actionable_recommendations=recommendations,
            )

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg="Dashboard analytics fetched successfully",
                data=dashboard_data.model_dump(),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error compiling dashboard analytics for user {user_id}: {e}", exc_info=True)
            raise ServerException(message=str(e))

    def _calculate_overall_resume_score(
        self, p_obj, s_obj, sk_obj, work_list, edu_obj, pr_obj
    ) -> tuple[int, Dict[str, int]]:
        score = 0
        breakdown = {}

        # 1. Personal Info (max 15 pts)
        p_score = 0
        if p_obj:
            if getattr(p_obj, "first_name", None) and getattr(p_obj, "last_name", None):
                p_score += 4
            if getattr(p_obj, "email", None) and getattr(p_obj, "phone", None):
                p_score += 4
            if getattr(p_obj, "city", None) or getattr(p_obj, "country", None):
                p_score += 3
            if getattr(p_obj, "linkedin", None) or getattr(p_obj, "github", None) or getattr(p_obj, "website", None):
                p_score += 4
        breakdown["personal_info"] = p_score
        score += p_score

        # 2. Professional Summary (max 15 pts)
        s_score = 0
        if s_obj:
            text = str(getattr(s_obj, "summary", "") or "")
            word_count = len(text.split())
            if word_count > 0:
                s_score += 6
            if word_count >= 25:
                s_score += 5
            if any(term in text.lower() for term in ("experience", "developer", "engineer", "lead", "architect", "skills", "proficient")):
                s_score += 4
        breakdown["professional_summary"] = s_score
        score += s_score

        # 3. Technical Skills (max 20 pts)
        sk_score = 0
        if sk_obj:
            categorized = structure_skills_into_categories(getattr(sk_obj, "skills", {}))
            count = sum(len(v) for v in categorized.values())
            if count >= 3:
                sk_score += 6
            if count >= 8:
                sk_score += 6
            if len(categorized) >= 3:
                sk_score += 8
        breakdown["skills"] = sk_score
        score += sk_score

        # 4. Work Experience (max 25 pts)
        w_score = 0
        if work_list and isinstance(work_list, list) and len(work_list) > 0:
            w_score += 10
            if len(work_list) >= 2 or calculate_candidate_experience_years(work_list) >= 1.0:
                w_score += 7
            # Action verbs & responsibilities
            all_text = " ".join([
                str(item.get("responsibilities", "")) + " " + str(item.get("achievements", ""))
                for item in work_list if isinstance(item, dict)
            ]).lower()
            if any(verb in all_text for verb in ACTION_VERBS):
                w_score += 8
        breakdown["work_experience"] = w_score
        score += w_score

        # 5. Projects (max 15 pts)
        pr_score = 0
        if pr_obj and getattr(pr_obj, "projects", None):
            projs = pr_obj.projects
            if isinstance(projs, list) and len(projs) > 0:
                pr_score += 8
                first_p = projs[0]
                if isinstance(first_p, dict) and (first_p.get("url") or len(str(first_p.get("description", "")).split()) >= 10):
                    pr_score += 7
        breakdown["projects"] = pr_score
        score += pr_score

        # 6. Education (max 10 pts)
        edu_score = 0
        if edu_obj and getattr(edu_obj, "educations", None):
            edus = edu_obj.educations
            if isinstance(edus, list) and len(edus) > 0:
                first_e = edus[0]
                if isinstance(first_e, dict):
                    if first_e.get("degree"):
                        edu_score += 6
                    if first_e.get("institution") or first_e.get("school_name"):
                        edu_score += 4
        breakdown["education"] = edu_score
        score += edu_score

        return min(100, max(0, score)), breakdown

    def _calculate_ats_parsing_rate(
        self, has_p, p_obj, has_s, s_obj, has_sk, has_w, work_list, has_edu, has_pr
    ) -> int:
        rate = 0
        # 1. Contact Info Cleanliness (20 pts)
        if has_p and p_obj:
            if getattr(p_obj, "email", None) and "@" in str(p_obj.email):
                rate += 10
            if getattr(p_obj, "phone", None):
                rate += 10

        # 2. Section Completeness & Standard Headers (30 pts)
        headers_count = sum([has_p, has_s, has_sk, has_w, has_edu, has_pr])
        rate += int((headers_count / 6.0) * 30)

        # 3. Parseable Work Experience Dates (25 pts)
        if has_w and work_list:
            rate += 15
            # Check if start and end dates are parseable
            has_dates = True
            for item in work_list:
                if isinstance(item, dict) and not item.get("start_date"):
                    has_dates = False
                    break
            if has_dates:
                rate += 10

        # 4. Standard bullet verbs & text readability (15 pts)
        if has_w and work_list:
            all_text = " ".join([
                str(item.get("responsibilities", "")) for item in work_list if isinstance(item, dict)
            ]).lower()
            if any(verb in all_text for verb in ACTION_VERBS):
                rate += 15
        elif has_s:
            rate += 10

        return min(98, max(20, rate))

    def _generate_recommendations(
        self, has_p, p_obj, has_s, s_obj, has_sk, total_skills_count, populated_cats,
        has_w, work_list, has_pr, pr_obj, total_jds, top_missing
    ) -> List[ActionableRecommendation]:
        recs = []

        # Personal Info Links
        if not (has_p and p_obj and (getattr(p_obj, "linkedin", None) or getattr(p_obj, "github", None))):
            recs.append(ActionableRecommendation(
                type="contact",
                priority="High",
                message="Add your LinkedIn profile or GitHub repository to boost recruiter discovery and credibility.",
            ))

        # Professional Summary
        if not (has_s and s_obj and len(str(getattr(s_obj, "summary", "")).split()) >= 25):
            recs.append(ActionableRecommendation(
                type="summary",
                priority="Medium",
                message="Enhance your Executive Summary with key technical specializations to improve ATS keyword ranking.",
            ))

        # Skills depth
        if total_skills_count < 10 or populated_cats < 4:
            recs.append(ActionableRecommendation(
                type="skills",
                priority="Medium",
                message="Broaden your technical skillset across at least 4 categories (e.g. Cloud & DevOps, Testing & QA) to qualify for senior roles.",
            ))

        # Work Experience Metrics
        if has_w and work_list:
            all_text = " ".join([
                str(item.get("responsibilities", "")) + " " + str(item.get("achievements", ""))
                for item in work_list if isinstance(item, dict)
            ])
            has_numbers = bool(re.search(r"\b\d+%\b|\b\d+x\b|\b\d+\s*(?:ms|users|projects|services|apis)\b", all_text, re.IGNORECASE))
            if not has_numbers:
                recs.append(ActionableRecommendation(
                    type="experience",
                    priority="High",
                    message="Add quantified metrics (e.g., 'reduced API latency by 35%', 'scaled to 50k users') to your bullet points to increase recruiter engagement.",
                ))

        # Job Description Tailoring
        if total_jds == 0:
            recs.append(ActionableRecommendation(
                type="tailoring",
                priority="High",
                message="Tailor your resume against target job descriptions using the JD Analyzer to double your interview shortlisting rate.",
            ))
        elif top_missing:
            recs.append(ActionableRecommendation(
                type="interview_prep",
                priority="Medium",
                message=f"Review interview preparation tips for your most frequent missing skill gaps: {', '.join(top_missing[:3])}.",
            ))

        return recs[:4]
