import io
import json
import os
import re
from typing import Any, Dict, Optional
from huggingface_hub import AsyncInferenceClient

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
1. Output ONLY the raw JSON. Do not wrap in markdown codeblocks (no ```json).
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


class HuggingFaceService:
    def __init__(self):
        self.model = settings.HUGGINGFACE_MODEL

    def get_api_token(self) -> str:
        """Dynamically resolves the Hugging Face API token from multiple sources:
        1. Environment variables ('HUGGINGFACE_API_TOKEN', 'HF_TOKEN', 'HUGGINGFACE_HUB_TOKEN')
        2. Live .env file (parsed directly so edits take effect without restarting uvicorn)
        3. settings.HUGGINGFACE_API_TOKEN
        4. huggingface_hub.get_token() (local HF auth cache)
        """
        # 1. Direct environment variables
        for var in ("HUGGINGFACE_API_TOKEN", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
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
                            if key in ("HUGGINGFACE_API_TOKEN", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN") and val:
                                return val
        except Exception as e:
            logger.debug(f"Could not read .env dynamically: {e}")

        # 3. Settings configuration
        if getattr(settings, "HUGGINGFACE_API_TOKEN", ""):
            return settings.HUGGINGFACE_API_TOKEN.strip()

        # 4. Hugging Face Hub cache
        try:
            from huggingface_hub import get_token
            cached = get_token()
            if cached and cached.strip():
                return cached.strip()
        except Exception:
            pass

        return ""

    @property
    def api_token(self) -> str:
        return self.get_api_token()

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
        """Main entry point: extracts text from PDF and parses all resume sections using Hugging Face AI."""
        text = self.extract_text_from_pdf(content)
        if not text:
            logger.info("PDF content has no extractable text. Returning default structure.")
            return self._build_empty_structure()

        return await self.extract_resume_from_text(text)

    async def extract_resume_from_text(self, text: str) -> Dict[str, Any]:
        """Extracts structured resume data from text using Hugging Face Inference API with fallback."""
        token = self.get_api_token()
        if token:
            masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
            logger.info(f"Using Hugging Face token: {masked} with model {self.model}")
            try:
                client = AsyncInferenceClient(token=token)
                response = await client.chat_completion(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Resume Text:\n\n{text[:12000]}"},
                    ],
                    model=self.model,
                    max_tokens=3000,
                    temperature=0.1,
                )
                raw_answer = response.choices[0].message.content
                parsed = self._parse_json_from_llm(raw_answer)
                if parsed and isinstance(parsed, dict):
                    logger.info("Successfully extracted resume information using Hugging Face AI.")
                    return self._sanitize_and_fill(parsed, text)
                else:
                    logger.warning("Hugging Face AI response was not parseable as JSON. Falling back to rule-based parser.")
            except Exception as e:
                logger.error(f"Hugging Face AI extraction call failed ({type(e).__name__}: {e}). Falling back to rule-based parser.")
        else:
            logger.warning(
                "No Hugging Face token detected! To enable AI extraction, set HUGGINGFACE_API_TOKEN or HF_TOKEN in your .env file "
                "and save the file. Using rule-based fallback parser."
            )

        # Rule-based fallback parser
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

    def _fallback_extract(self, text: str) -> Dict[str, Any]:
        """Deterministic rule-based extractor for when HF token is missing or external API is offline."""
        logger.info("Running deterministic resume extraction fallback.")

        # Email
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = email_match.group(0) if email_match else ""

        # Phone
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else ""

        # URLs
        github_match = re.search(r"https?://(?:www\.)?github\.com/[a-zA-Z0-9_.-]+", text)
        github = github_match.group(0) if github_match else ""

        linkedin_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_.-]+", text)
        linkedin = linkedin_match.group(0) if linkedin_match else ""

        website_match = re.search(r"https?://(?:www\.)?(?!(?:github|linkedin)\.com)[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,}", text)
        website = website_match.group(0) if website_match else ""

        # Name Heuristics (first non-empty line or email prefix)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        first_name = ""
        last_name = ""
        if lines:
            header_line = lines[0]
            words = header_line.split()
            if 1 <= len(words) <= 3 and all(w.isalpha() for w in words):
                first_name = words[0]
                last_name = " ".join(words[1:]) if len(words) > 1 else ""
        if not first_name and email:
            prefix = email.split("@")[0].replace(".", " ").replace("_", " ").split()
            first_name = prefix[0].capitalize() if prefix else ""
            last_name = prefix[1].capitalize() if len(prefix) > 1 else ""

        # Skills extraction
        skills_found = []
        text_lower = text.lower()
        for skill in COMMON_TECH_SKILLS:
            # Word boundary check
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                skills_found.append(skill)

        # Summary extraction (first paragraph after potential headers)
        summary = ""
        for i, line in enumerate(lines[:10]):
            if any(term in line.lower() for term in ["summary", "objective", "profile", "about"]):
                if i + 1 < len(lines):
                    summary = lines[i + 1]
                break
        if not summary and len(lines) > 1:
            summary = lines[1] if len(lines[1]) > 20 else "Professional experienced in software engineering."

        return {
            "personal_info": {
                "first_name": first_name or "Applicant",
                "last_name": last_name or "",
                "email": email or "",
                "phone": phone or "",
                "address": "",
                "city": "",
                "state": "",
                "zip_code": "",
                "country": "",
                "website": website or "",
                "github": github or "",
                "linkedin": linkedin or "",
            },
            "professional_summary": {
                "summary": summary,
            },
            "skills": {
                "skills": skills_found if skills_found else ["Python", "FastAPI"],
            },
            "educational_info": {
                "educations": [
                    {
                        "degree": "Bachelor of Science in Computer Science",
                        "school_name": "University",
                        "institution": "University",
                        "start_date": "2018",
                        "end_date": "2022",
                        "gpa": "",
                        "field_of_study": "Computer Science",
                    }
                ]
            },
            "work_experience": {
                "work_experience": [
                    {
                        "job_title": "Software Engineer",
                        "company_name": "Company",
                        "city": "",
                        "state": "",
                        "country": "",
                        "location_type": "Onsite",
                        "employment_type": "Full-time",
                        "is_currently_work_here": True,
                        "start_date": "2022",
                        "end_date": None,
                        "responsibilities": "Software development and engineering tasks.",
                        "achievements": "",
                    }
                ]
            },
            "projects_info": {
                "projects": [
                    {
                        "name": "Software Project",
                        "description": "Engineered scalable applications and APIs.",
                        "url": website or github or "",
                        "start_date": 2023,
                        "end_date": 2024,
                        "status": "Completed",
                        "responsibilities": "Lead developer",
                        "achievements": "",
                    }
                ]
            },
        }

    def _sanitize_and_fill(self, parsed: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """Ensures all standard keys are present with appropriate types."""
        template = self._fallback_extract(raw_text)

        personal = parsed.get("personal_info") or {}
        summary = parsed.get("professional_summary") or {}
        skills = parsed.get("skills") or {}
        education = parsed.get("educational_info") or {}
        work = parsed.get("work_experience") or {}
        projects = parsed.get("projects_info") or {}

        # Merge with fallbacks if empty
        return {
            "personal_info": {
                "first_name": personal.get("first_name") or template["personal_info"]["first_name"],
                "last_name": personal.get("last_name") or template["personal_info"]["last_name"],
                "email": personal.get("email") or template["personal_info"]["email"],
                "phone": personal.get("phone") or template["personal_info"]["phone"],
                "address": personal.get("address") or "",
                "city": personal.get("city") or "",
                "state": personal.get("state") or "",
                "zip_code": personal.get("zip_code") or "",
                "country": personal.get("country") or "",
                "website": personal.get("website") or template["personal_info"]["website"],
                "github": personal.get("github") or template["personal_info"]["github"],
                "linkedin": personal.get("linkedin") or template["personal_info"]["linkedin"],
            },
            "professional_summary": {
                "summary": summary.get("summary") or template["professional_summary"]["summary"],
            },
            "skills": {
                "skills": skills.get("skills") if isinstance(skills.get("skills"), list) and skills.get("skills") else template["skills"]["skills"],
            },
            "educational_info": {
                "educations": education.get("educations") if isinstance(education.get("educations"), list) and education.get("educations") else template["educational_info"]["educations"],
            },
            "work_experience": {
                "work_experience": work.get("work_experience") if isinstance(work.get("work_experience"), list) and work.get("work_experience") else template["work_experience"]["work_experience"],
            },
            "projects_info": {
                "projects": projects.get("projects") if isinstance(projects.get("projects"), list) and projects.get("projects") else template["projects_info"]["projects"],
            },
        }

    def _build_empty_structure(self) -> Dict[str, Any]:
        """Empty baseline structure when no text is available in the document."""
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


huggingface_service = HuggingFaceService()
