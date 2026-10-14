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


gemini_service = GeminiService()
