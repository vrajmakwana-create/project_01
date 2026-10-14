import io
import json
import os
import re
from typing import Any, Dict, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert AI Resume Parsing Engine.
Analyze the provided resume text and extract all information into a strict, valid JSON object matching this exact schema:

{
  "personal_info": {
    "first_name": "...",
    "last_name": "...",
    "email": "...",
    "phone": "...",
    "address": "...",
    "city": "...",
    "state": "...",
    "zip_code": "...",
    "country": "...",
    "website": "...",
    "github": "...",
    "linkedin": "..."
  },
  "professional_summary": {
    "summary": "..."
  },
  "skills": {
    "skills": ["Skill 1", "Skill 2"]
  },
  "educational_info": {
    "educations": [
      {
        "degree": "...",
        "school_name": "...",
        "institution": "...",
        "start_date": "...",
        "end_date": "...",
        "gpa": "...",
        "field_of_study": "..."
      }
    ]
  },
  "work_experience": {
    "work_experience": [
      {
        "job_title": "...",
        "company_name": "...",
        "city": "...",
        "state": "...",
        "country": "...",
        "location_type": "...",
        "employment_type": "...",
        "is_currently_work_here": false,
        "start_date": "...",
        "end_date": "...",
        "responsibilities": "...",
        "achievements": "..."
      }
    ]
  },
  "projects_info": {
    "projects": [
      {
        "name": "...",
        "description": "...",
        "url": "...",
        "start_date": 2022,
        "end_date": 2023,
        "status": "...",
        "responsibilities": "...",
        "achievements": "..."
      }
    ]
  }
}

Rules:
1. Output ONLY a valid JSON object matching this schema.
2. If any field is not found in the resume text, provide "" for string or [] for list.
3. Keep the keys and nesting exactly as specified.
"""

COMMON_TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin",
    "FastAPI", "Django", "Flask", "React", "Next.js", "Vue", "Angular", "Node.js", "Express", "Spring Boot",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Elasticsearch", "Cassandra",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "CI/CD", "Linux", "Git", "GitHub", "GitLab",
    "REST", "GraphQL", "gRPC", "Microservices", "Machine Learning", "PyTorch", "TensorFlow", "Pandas", "NumPy"
]

JD_ANALYSIS_SYSTEM_PROMPT = """You are an elite AI Career Strategist, Technical Recruiter, and Resume Optimization Engine.
Analyze the target Job Description (JD) against the Candidate's Current Resume profile.

Your tasks:
1. Extract Job Metadata & Seniority/Experience:
   - Identify or extract job title and company name from the JD if not provided.
   - Detect required years of experience in the JD (e.g. 7.0 for "7+ years", 3.0 for "3-5 years", etc.).
   - Estimate candidate's total years of experience from their work experience history.
   - Determine seniority level of the JD (e.g., "Senior / Lead", "Mid-Level", "Junior / Entry-Level").
   - Determine candidate's current seniority level (e.g., "Mid-Level", "Junior", "Senior").
   - Formulate an insightful, candid `experience_gap_verdict`. For example, if the JD requires 7 years (Senior) and the candidate has 3 years (Mid-Level):
     "Seniority Alert: This position requires Senior-level experience (7+ years) while your current profile reflects ~3 years. Focus heavily on demonstrating high-impact ownership, architecture decisions, and mentoring experience in your resume bullets, and thoroughly prepare for senior system design interviews."
2. Extract and Categorize Skills:
   - `extracted_jd_skills`: All relevant technical, domain, and core competency skills extracted from the JD.
   - `matching_skills`: Skills that the candidate ALREADY possesses (found in candidate resume).
   - `missing_skills`: Critical skills demanded by the JD that the candidate currently LACKS (skills difference for interview preparation).
3. Compute ATS Match Score:
   - `match_score`: An integer from 0 to 100 representing how closely the candidate's existing background aligns with the JD.
   - `match_rationale`: 2-3 sentences explaining the score breakdown.
4. Generate Interview Preparation Guide for Missing Skills:
   - For each missing skill (up to 8 highest-priority ones):
     - `skill`: Name of the skill.
     - `priority`: "High", "Medium", or "Low".
     - `why_important`: Why the hiring team specifically needs this skill according to the JD.
     - `key_concepts_to_revise`: Top 3-5 core technical concepts/topics to study.
     - `likely_interview_questions`: Top 3 realistic interview questions testing this skill.
5. Generate JD-Tailored Resume Content (100% Relevance for ATS Shortlisting):
   - `tailored_summary`: An impactful 3-4 sentence professional summary tailored precisely to the JD, embedding key JD terms, matching strengths, and candidate domain relevance to maximize ATS shortlisting without fabricating false claims.
   - `tailored_skills`: An optimized, deduplicated list of skills strategically arranged with JD priority keywords and matching candidate proficiencies. Provide pure, clean skill names only (e.g. ["Python", "FastAPI", "Kubernetes", "AWS"]). Do NOT append any notes, brackets, or parenthetical annotations like "(Interview Focus)" or "(Learning)".

Return ONLY a strict JSON object matching this schema:
{
  "job_title": "...",
  "company_name": "...",
  "match_score": 85,
  "match_rationale": "...",
  "jd_experience_years": 7.0,
  "candidate_experience_years": 3.0,
  "seniority_level_jd": "Senior / Lead",
  "seniority_level_candidate": "Mid-Level",
  "experience_gap_verdict": "...",
  "extracted_jd_skills": ["..."],
  "matching_skills": ["..."],
  "missing_skills": ["..."],
  "interview_preparation_tips": [
    {
      "skill": "...",
      "priority": "High",
      "why_important": "...",
      "key_concepts_to_revise": ["..."],
      "likely_interview_questions": ["..."]
    }
  ],
  "tailored_summary": "...",
  "tailored_skills": ["..."]
}
"""


class GeminiService:
    def __init__(self):
        pass

    def get_model(self) -> str:
        """Dynamically resolves the Google Gemini model:
        1. Environment variable 'GEMINI_MODEL'
        2. Live .env file
        3. settings.GEMINI_MODEL
        Maps any 'live' models to 'gemini-3-flash-preview' because Google Live models
        are WebSocket-only audio streaming models that reject document generateContent calls.
        """
        model = os.getenv("GEMINI_MODEL", "")
        if not model:
            try:
                env_path = os.path.join(os.getcwd(), ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("GEMINI_MODEL="):
                                model = line.split("=", 1)[1].strip().strip("'\"")
                                break
            except Exception:
                pass

        if not model:
            model = getattr(settings, "GEMINI_MODEL", "") or "gemini-3-flash-preview"

        model = model.strip()

        # Handle 'Gemini 3 Flash Live' or any '-live' WebSocket models
        if "live" in model.lower():
            logger.info(
                f"Model '{model}' is a real-time WebSocket audio model. "
                "Auto-routing to 'gemini-3-flash-preview' for document extraction."
            )
            return "gemini-3-flash-preview"

        return model

    @property
    def model(self) -> str:
        return self.get_model()

    def get_api_key(self) -> str:
        """Dynamically resolves the Google Gemini API key from multiple sources:
        1. Environment variables ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GEMINI_API_KEY')
        2. Live .env file (parsed on demand so changes take effect immediately without uvicorn reload)
        3. settings.GEMINI_API_KEY
        """
        # 1. Environment variables
        for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"):
            val = os.getenv(var)
            if val and val.strip():
                return val.strip()

        # 2. Live read of .env file
        try:
            env_path = os.path.join(os.getcwd(), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, _, val = line.partition("=")
                            key = key.strip().upper()
                            val = val.strip().strip("'\"")
                            if key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY") and val:
                                return val
        except Exception as e:
            logger.debug(f"Could not read .env dynamically: {e}")

        # 3. Settings configuration
        if getattr(settings, "GEMINI_API_KEY", ""):
            return settings.GEMINI_API_KEY.strip()

        return ""

    @property
    def api_key(self) -> str:
        return self.get_api_key()

    def extract_text_from_pdf(self, content: bytes) -> str:
        """Extracts plain text content from PDF binary bytes using pypdf with robust fallback."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
            if pages_text:
                return "\n".join(pages_text).strip()
        except Exception as e:
            logger.warning(f"pypdf reader extraction encountered: {e}. Trying raw string fallback.")

        # Fallback to extracting printable UTF-8 or ASCII string chunks
        try:
            raw_text = content.decode("utf-8", errors="ignore")
            cleaned = "".join(ch for ch in raw_text if ch.isprintable() or ch in "\n\r\t ")
            if len(cleaned.strip()) > 10:
                return cleaned.strip()
        except Exception:
            pass
        return ""

    async def extract_resume_from_pdf(self, content: bytes) -> Dict[str, Any]:
        """Main entry point: extracts text from PDF and parses all resume sections using Google Gemini AI."""
        text = self.extract_text_from_pdf(content)
        if not text:
            logger.info("PDF content has no extractable text. Returning default structure.")
            return self._build_empty_structure()

        return await self.extract_resume_from_text(text)

    async def extract_resume_from_text(self, text: str) -> Dict[str, Any]:
        """Extracts structured resume data from text using Google Gemini AI with fallback."""
        api_key = self.get_api_key()
        active_model = self.get_model()

        if api_key:
            masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            logger.info(f"Using Google Gemini AI (model={active_model}, key={masked})")
            client = genai.Client(api_key=api_key)

            for target_model in [active_model, "gemini-3-flash-preview"]:
                try:
                    response = await client.aio.models.generate_content(
                        model=target_model,
                        contents=f"Resume Text:\n\n{text[:20000]}",
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.1,
                        ),
                    )
                    raw_answer = response.text or ""
                    parsed = self._parse_json_from_llm(raw_answer)
                    if parsed and isinstance(parsed, dict):
                        logger.info(f"Successfully extracted resume information using Google Gemini ({target_model}).")
                        return self._sanitize_and_fill(parsed, text)
                    else:
                        logger.warning(f"Gemini AI ({target_model}) response was not parseable as JSON.")
                except Exception as e:
                    logger.warning(f"Gemini AI ({target_model}) call failed ({type(e).__name__}: {e}).")
                    if target_model == "gemini-3-flash-preview":
                        logger.error("All Gemini AI attempts failed. Falling back to rule-based parser.")
        else:
            logger.warning(
                "No Google Gemini API key detected! Set GEMINI_API_KEY in your .env file and save it. "
                "Using rule-based fallback parser."
            )

        # Rule-based deterministic fallback parser
        return self._fallback_extract(text)

    def _parse_json_from_llm(self, content: str) -> Optional[Dict[str, Any]]:
        """Parses LLM response into a valid python dict, stripping code fences if present."""
        text = content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None

    def _build_empty_structure(self) -> Dict[str, Any]:
        """Builds a complete, empty schema-compliant dictionary."""
        return {
            "personal_info": {
                "first_name": "",
                "last_name": "",
                "email": "",
                "phone": "",
                "address": "",
                "city": "",
                "state": "",
                "zip_code": "",
                "country": "",
                "website": "",
                "github": "",
                "linkedin": "",
            },
            "professional_summary": {"summary": ""},
            "skills": {"skills": []},
            "educational_info": {"educations": []},
            "work_experience": {"work_experience": []},
            "projects_info": {"projects": []},
        }

    def _sanitize_and_fill(self, data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """Ensures all 6 sections exist and comply with expected structure and types."""
        out = self._build_empty_structure()

        # 1. Personal Info
        p = data.get("personal_info") or {}
        if isinstance(p, dict):
            for k in out["personal_info"].keys():
                val = p.get(k)
                out["personal_info"][k] = str(val).strip() if val is not None else ""

        # 2. Professional Summary
        summary = data.get("professional_summary") or {}
        if isinstance(summary, dict):
            out["professional_summary"]["summary"] = str(summary.get("summary") or "").strip()
        elif isinstance(summary, str):
            out["professional_summary"]["summary"] = summary.strip()

        # 3. Skills
        skills = data.get("skills") or {}
        if isinstance(skills, dict):
            sk_list = skills.get("skills") or []
            if isinstance(sk_list, list):
                out["skills"]["skills"] = [str(s).strip() for s in sk_list if s and str(s).strip()]
        elif isinstance(skills, list):
            out["skills"]["skills"] = [str(s).strip() for s in skills if s and str(s).strip()]

        # 4. Educational Info
        edu = data.get("educational_info") or {}
        if isinstance(edu, dict):
            edu_list = edu.get("educations") or []
            if isinstance(edu_list, list):
                cleaned_edus = []
                for item in edu_list:
                    if isinstance(item, dict):
                        cleaned_edus.append({
                            "degree": str(item.get("degree") or ""),
                            "school_name": str(item.get("school_name") or item.get("institution") or ""),
                            "institution": str(item.get("institution") or item.get("school_name") or ""),
                            "start_date": str(item.get("start_date") or ""),
                            "end_date": str(item.get("end_date") or ""),
                            "gpa": str(item.get("gpa") or "") if item.get("gpa") else None,
                            "field_of_study": str(item.get("field_of_study") or "") if item.get("field_of_study") else None,
                        })
                out["educational_info"]["educations"] = cleaned_edus

        # 5. Work Experience
        work = data.get("work_experience") or {}
        if isinstance(work, dict):
            work_list = work.get("work_experience") or []
            if isinstance(work_list, list):
                cleaned_works = []
                for item in work_list:
                    if isinstance(item, dict):
                        cleaned_works.append({
                            "job_title": str(item.get("job_title") or ""),
                            "company_name": str(item.get("company_name") or ""),
                            "city": str(item.get("city") or ""),
                            "state": str(item.get("state") or ""),
                            "country": str(item.get("country") or ""),
                            "location_type": str(item.get("location_type") or "Onsite"),
                            "employment_type": str(item.get("employment_type") or "Full-time"),
                            "is_currently_work_here": bool(item.get("is_currently_work_here", False)),
                            "start_date": str(item.get("start_date") or ""),
                            "end_date": str(item.get("end_date") or "") if not item.get("is_currently_work_here") else None,
                            "responsibilities": str(item.get("responsibilities") or ""),
                            "achievements": str(item.get("achievements") or ""),
                        })
                out["work_experience"]["work_experience"] = cleaned_works

        # 6. Projects Info
        proj = data.get("projects_info") or {}
        if isinstance(proj, dict):
            proj_list = proj.get("projects") or []
            if isinstance(proj_list, list):
                cleaned_projs = []
                for item in proj_list:
                    if isinstance(item, dict):
                        s_date = item.get("start_date")
                        e_date = item.get("end_date")
                        try:
                            s_date = int(s_date) if s_date else None
                        except (ValueError, TypeError):
                            s_date = None
                        try:
                            e_date = int(e_date) if e_date else None
                        except (ValueError, TypeError):
                            e_date = None

                        cleaned_projs.append({
                            "name": str(item.get("name") or ""),
                            "description": str(item.get("description") or ""),
                            "url": str(item.get("url") or "") if item.get("url") else None,
                            "start_date": s_date,
                            "end_date": e_date,
                            "status": str(item.get("status") or "Completed"),
                            "responsibilities": str(item.get("responsibilities") or ""),
                            "achievements": str(item.get("achievements") or ""),
                        })
                out["projects_info"]["projects"] = cleaned_projs

        return out

    def _fallback_extract(self, text: str) -> Dict[str, Any]:
        """Deterministic rule-based extractor using regex and pattern matching."""
        logger.info("Running deterministic resume extraction fallback.")
        result = self._build_empty_structure()

        # --- Personal Info extraction ---
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        if email_match:
            result["personal_info"]["email"] = email_match.group(0)

        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        if phone_match:
            result["personal_info"]["phone"] = phone_match.group(0).strip()

        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+", text)
        if github_match:
            result["personal_info"]["github"] = github_match.group(0)

        linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+", text)
        if linkedin_match:
            result["personal_info"]["linkedin"] = linkedin_match.group(0)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines:
            first_line = lines[0]
            words = first_line.split()
            if 1 < len(words) <= 3 and all(w.isalpha() for w in words):
                result["personal_info"]["first_name"] = words[0]
                result["personal_info"]["last_name"] = " ".join(words[1:])
            elif words and words[0].isalpha():
                result["personal_info"]["first_name"] = words[0]

        # --- Professional Summary extraction ---
        summary_match = re.search(
            r"(?:summary|profile|about me|objective)[:\s\n]+(.*?)(?=\n\s*(?:skills|experience|education|projects)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if summary_match:
            clean_summary = re.sub(r"\s+", " ", summary_match.group(1)).strip()
            result["professional_summary"]["summary"] = clean_summary[:1000]

        # --- Skills extraction ---
        found_skills = set()
        for skill in COMMON_TECH_SKILLS:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.add(skill)
        result["skills"]["skills"] = sorted(list(found_skills))

        # --- Education extraction ---
        edu_matches = re.finditer(
            r"(?:bachelor|master|phd|b\.s\.|m\.s\.|b\.e\.|b\.tech|m\.tech|degree|university|college|institute)[\w\s,.-]+",
            text,
            re.IGNORECASE,
        )
        educations = []
        for m in list(edu_matches)[:3]:
            chunk = m.group(0).strip()
            if len(chunk) > 5:
                degree = "Degree"
                school = chunk
                if "bachelor" in chunk.lower() or "b.s." in chunk.lower() or "b.tech" in chunk.lower():
                    degree = "Bachelor's"
                elif "master" in chunk.lower() or "m.s." in chunk.lower() or "m.tech" in chunk.lower():
                    degree = "Master's"
                educations.append({
                    "degree": degree,
                    "school_name": school[:100],
                    "institution": school[:100],
                    "start_date": "",
                    "end_date": "",
                    "gpa": None,
                    "field_of_study": None,
                })
        result["educational_info"]["educations"] = educations

        return result

    async def analyze_jd_and_tailor_resume(
        self,
        jd_text: str,
        current_resume: Dict[str, Any],
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyzes a job description against the candidate's resume:
        - Extracts skills and seniority requirements from the JD
        - Compares experience years (e.g. 7 yrs required vs 3 yrs candidate)
        - Computes matching skills vs missing skills (interview prep gap)
        - Generates tailored resume summary and skills for high ATS relevance
        - Builds an interview preparation guide for missing skills
        """
        api_key = self.get_api_key()
        active_model = self.get_model()

        candidate_summary = ""
        summary_obj = current_resume.get("professional_summary")
        if isinstance(summary_obj, dict):
            candidate_summary = summary_obj.get("summary", "")
        elif isinstance(summary_obj, str):
            candidate_summary = summary_obj

        candidate_skills = []
        skills_obj = current_resume.get("skills")
        if isinstance(skills_obj, dict):
            candidate_skills = skills_obj.get("skills", [])
        elif isinstance(skills_obj, list):
            candidate_skills = skills_obj

        work_exp = current_resume.get("work_experience") or []
        if isinstance(work_exp, dict):
            work_exp = work_exp.get("work_experience", [])

        projects = current_resume.get("projects_info") or []
        if isinstance(projects, dict):
            projects = projects.get("projects", [])

        prompt_context = (
            f"Target Job Description:\n{jd_text[:12000]}\n\n"
            f"Provided Job Title: {job_title or 'Auto-detect from JD'}\n"
            f"Provided Company Name: {company_name or 'Auto-detect from JD'}\n\n"
            f"Candidate Current Resume Profile:\n"
            f"- Current Professional Summary: {candidate_summary}\n"
            f"- Current Skills: {json.dumps(candidate_skills)}\n"
            f"- Work Experience History: {json.dumps(work_exp[:6])}\n"
            f"- Projects: {json.dumps(projects[:6])}\n"
        )

        if api_key:
            masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            logger.info(f"Analyzing JD with Google Gemini AI (model={active_model}, key={masked})")
            client = genai.Client(api_key=api_key)

            for target_model in [active_model, "gemini-3-flash-preview"]:
                try:
                    response = await client.aio.models.generate_content(
                        model=target_model,
                        contents=prompt_context,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            system_instruction=JD_ANALYSIS_SYSTEM_PROMPT,
                            temperature=0.2,
                        ),
                    )
                    raw_answer = response.text or ""
                    parsed = self._parse_json_from_llm(raw_answer)
                    if parsed and isinstance(parsed, dict) and "extracted_jd_skills" in parsed:
                        logger.info(f"Successfully analyzed JD using Google Gemini ({target_model}).")
                        return self._sanitize_jd_analysis(
                            parsed,
                            jd_text=jd_text,
                            current_resume=current_resume,
                            job_title=job_title,
                            company_name=company_name,
                        )
                except Exception as e:
                    logger.warning(f"Gemini AI ({target_model}) JD analysis call failed ({type(e).__name__}: {e}).")

        # Deterministic fallback parser
        logger.info("Using deterministic fallback for JD analysis.")
        return self._fallback_analyze_jd(
            jd_text=jd_text,
            current_resume=current_resume,
            job_title=job_title,
            company_name=company_name,
        )

    def _sanitize_jd_analysis(
        self,
        data: Dict[str, Any],
        jd_text: str,
        current_resume: Dict[str, Any],
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cleans and validates the JD analysis output from Gemini."""
        final_job_title = job_title or str(data.get("job_title") or "Target Role").strip()
        final_company = company_name or str(data.get("company_name") or "").strip() or None

        try:
            score = int(data.get("match_score", 70))
            score = max(0, min(100, score))
        except Exception:
            score = 70

        jd_exp = data.get("jd_experience_years")
        cand_exp = data.get("candidate_experience_years")
        try:
            jd_exp = float(jd_exp) if jd_exp is not None else None
        except Exception:
            jd_exp = None
        try:
            cand_exp = float(cand_exp) if cand_exp is not None else None
        except Exception:
            cand_exp = None

        extracted_skills = [
            str(s).strip() for s in (data.get("extracted_jd_skills") or []) if s and str(s).strip()
        ]
        matching_skills = [
            str(s).strip() for s in (data.get("matching_skills") or []) if s and str(s).strip()
        ]
        missing_skills = [
            str(s).strip() for s in (data.get("missing_skills") or []) if s and str(s).strip()
        ]

        # Ensure missing skills truly reflect difference
        if not missing_skills and extracted_skills and matching_skills:
            matching_lower = {s.lower() for s in matching_skills}
            missing_skills = [s for s in extracted_skills if s.lower() not in matching_lower]

        tips = []
        raw_tips = data.get("interview_preparation_tips") or []
        if isinstance(raw_tips, list):
            for item in raw_tips:
                if isinstance(item, dict) and item.get("skill"):
                    tips.append({
                        "skill": str(item.get("skill")),
                        "priority": str(item.get("priority") or "High"),
                        "why_important": str(item.get("why_important") or ""),
                        "key_concepts_to_revise": [
                            str(k) for k in (item.get("key_concepts_to_revise") or [])
                        ],
                        "likely_interview_questions": [
                            str(q) for q in (item.get("likely_interview_questions") or [])
                        ],
                    })

        tailored_summary = str(data.get("tailored_summary") or "").strip()
        raw_tailored_skills = data.get("tailored_skills") or []
        tailored_skills = []
        seen_tailored = set()
        for s in raw_tailored_skills:
            clean_s = re.sub(r"\s*\(.*?\)", "", str(s)).strip()
            if clean_s and clean_s.lower() not in seen_tailored:
                seen_tailored.add(clean_s.lower())
                tailored_skills.append(clean_s)

        return {
            "job_title": final_job_title,
            "company_name": final_company,
            "match_score": score,
            "match_rationale": str(data.get("match_rationale") or "").strip(),
            "jd_experience_years": jd_exp,
            "candidate_experience_years": cand_exp,
            "seniority_level_jd": str(data.get("seniority_level_jd") or "").strip() or None,
            "seniority_level_candidate": str(data.get("seniority_level_candidate") or "").strip() or None,
            "experience_gap_verdict": str(data.get("experience_gap_verdict") or "").strip() or None,
            "extracted_jd_skills": extracted_skills,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "interview_preparation_tips": tips,
            "tailored_summary": tailored_summary,
            "tailored_skills": tailored_skills,
        }

    def _fallback_analyze_jd(
        self,
        jd_text: str,
        current_resume: Dict[str, Any],
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deterministic rule-based JD analysis fallback with experience gap and interview prep."""
        # 1. Experience Years extraction from JD
        jd_exp_match = re.search(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years?|yrs?)", jd_text, re.IGNORECASE)
        jd_exp_years: Optional[float] = None
        if jd_exp_match:
            try:
                jd_exp_years = float(jd_exp_match.group(1))
            except Exception:
                jd_exp_years = None

        # 2. Candidate experience estimation
        work_list = current_resume.get("work_experience") or []
        if isinstance(work_list, dict):
            work_list = work_list.get("work_experience", [])
        cand_exp_years = max(1.0, float(len(work_list)) * 1.5) if work_list else 2.0

        # Seniority levels
        def get_seniority(years: Optional[float]) -> str:
            if years is None:
                return "Not Specified"
            if years >= 6.0:
                return "Senior / Lead"
            elif years >= 3.0:
                return "Mid-Level"
            return "Junior / Entry-Level"

        jd_seniority = get_seniority(jd_exp_years)
        cand_seniority = get_seniority(cand_exp_years)

        # Experience gap verdict
        if jd_exp_years and jd_exp_years > (cand_exp_years + 1.0):
            gap_verdict = (
                f"Seniority Alert: This position requires {jd_seniority} experience ({int(jd_exp_years)}+ years), "
                f"while your current profile reflects ~{cand_exp_years:.1f} years ({cand_seniority}). "
                "Tailor your resume to highlight high-impact ownership, architecture decisions, and mentoring, "
                "and thoroughly prepare for senior system design and leadership questions."
            )
        elif jd_exp_years:
            gap_verdict = (
                f"Seniority Alignment: Your experience (~{cand_exp_years:.1f} years) matches the target "
                f"role's requirement ({int(jd_exp_years)}+ years, {jd_seniority})."
            )
        else:
            gap_verdict = "Experience requirement not explicitly specified in JD text."

        # 3. Detect Skills from JD
        found_jd_skills = []
        for skill in COMMON_TECH_SKILLS:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, jd_text, re.IGNORECASE):
                found_jd_skills.append(skill)

        if not found_jd_skills:
            found_jd_skills = ["Problem Solving", "Software Engineering", "Communication", "System Design"]

        # 4. Compare with Candidate Skills
        cand_skills = current_resume.get("skills") or []
        if isinstance(cand_skills, dict):
            cand_skills = cand_skills.get("skills", [])
        cand_skill_lower = {str(s).strip().lower(): str(s).strip() for s in cand_skills if s}

        matching = []
        missing = []
        for sk in found_jd_skills:
            if sk.lower() in cand_skill_lower:
                matching.append(sk)
            else:
                missing.append(sk)

        # Match Score
        score = int((len(matching) / max(len(found_jd_skills), 1)) * 100)
        score = max(25, min(95, score))

        # 5. Interview preparation tips for missing skills
        tips = []
        for sk in missing[:6]:
            tips.append({
                "skill": sk,
                "priority": "High" if len(tips) < 3 else "Medium",
                "why_important": f"The job description explicitly highlights {sk} as a core competency for delivering production projects.",
                "key_concepts_to_revise": [
                    f"Fundamental architecture, syntax, and lifecycle in {sk}",
                    f"Concurrency, memory, and performance best practices in {sk}",
                    f"Common debugging patterns and anti-patterns with {sk}",
                ],
                "likely_interview_questions": [
                    f"How would you design and implement a scalable module using {sk}?",
                    f"What key trade-offs and edge cases must be handled when deploying {sk}?",
                    f"Explain a challenging technical bug you might encounter in {sk} and how to fix it.",
                ],
            })

        # 6. Tailored Summary & Tailored Skills
        summary_obj = current_resume.get("professional_summary") or {}
        orig_summary = summary_obj.get("summary", "") if isinstance(summary_obj, dict) else str(summary_obj)
        role_label = job_title or "Target Role"

        tailored_summary = (
            f"Results-driven software professional experienced in {', '.join(matching[:3]) if matching else 'full-lifecycle engineering'}. "
            f"Demonstrated track record of delivering resilient, high-quality systems with proficiency in {', '.join(matching[:2]) if matching else 'software architecture'}. "
            f"Highly adaptive with rapid mastery of {', '.join(missing[:2]) if missing else 'modern toolchains'}, focused on driving immediate engineering impact for the {role_label} position."
        )

        seen_skills = set()
        tailored_skills = []
        for sk in matching + missing + [s for s in cand_skills if s]:
            clean_sk = re.sub(r"\s*\(.*?\)", "", str(sk)).strip()
            if clean_sk and clean_sk.lower() not in seen_skills:
                seen_skills.add(clean_sk.lower())
                tailored_skills.append(clean_sk)

        return {
            "job_title": job_title or "Target Role",
            "company_name": company_name,
            "match_score": score,
            "match_rationale": f"Candidate matches {len(matching)} out of {len(found_jd_skills)} key skills identified in the Job Description.",
            "jd_experience_years": jd_exp_years,
            "candidate_experience_years": cand_exp_years,
            "seniority_level_jd": jd_seniority,
            "seniority_level_candidate": cand_seniority,
            "experience_gap_verdict": gap_verdict,
            "extracted_jd_skills": found_jd_skills,
            "matching_skills": matching,
            "missing_skills": missing,
            "interview_preparation_tips": tips,
            "tailored_summary": tailored_summary,
            "tailored_skills": tailored_skills,
        }


gemini_service = GeminiService()
