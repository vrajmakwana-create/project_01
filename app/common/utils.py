import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import secrets
from typing import Optional, Tuple
from datetime import datetime, timezone
from pydantic import EmailStr
from app.services.email_service import email_service
from app.core.logger import get_logger

logger = get_logger(__name__)


def get_unix_time() -> int:
    """Return UNIX TIME in milliseconds."""
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def generate_otp() -> int:
    """Return cryptographically secure 6-digit random number (100000 to 999999)."""
    return 100000 + secrets.randbelow(900000)


async def send_email_verification_email(
    email: EmailStr,
    full_name: str,
    otp: Optional[int] = None,
    otp_expiry: Optional[int] = None,
) -> Tuple[int, int]:
    """Sends OTP verification email in background and returns (otp, otp_expiry)."""
    if otp is None or otp_expiry is None:
        otp_expiry = get_unix_time() + (5 * 60 * 1000)  # 5 minutes in ms
        otp = generate_otp()

    try:
        await email_service.send_otp_email(
            to_email=email,
            otp=otp,
            name=full_name,
        )
    except Exception as e:
        logger.error(f"Error dispatching background verification email to {email}: {e}", exc_info=True)

    return otp, otp_expiry


ORDERED_SKILL_CATEGORIES = [
    "Programming Languages",
    "Frameworks & Libraries",
    "Databases",
    "Tools & Technologies",
    "Cloud & DevOps",
    "Web Development",
    "AI & Machine Learning",
    "Data Analysis & Visualization",
    "Testing & QA",
    "Operating Systems",
]


def parse_date_to_ms(val: Any) -> Optional[float]:
    """Parses various date formats into epoch milliseconds (float).
    Handles millisecond timestamps (int/float), epoch seconds, YYYY-MM-DD, YYYY-MM, YYYYMMDD, and Month YYYY.
    """
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        # If timestamp is in seconds (e.g. 10 digits < 1e11), convert to milliseconds
        if val < 1e11:
            return float(val * 1000)
        return float(val)
    val_str = str(val).strip()
    if val_str.lower() in ("present", "current", "now", "ongoing"):
        return time.time() * 1000.0
    if re.match(r"^\d+(\.\d+)?$", val_str):
        num = float(val_str)
        if num < 1e11:
            return num * 1000.0
        return num
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y%m%d", "%b %Y", "%B %Y", "%Y"):
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.replace(tzinfo=timezone.utc).timestamp() * 1000.0
        except ValueError:
            pass
    return None


def validate_work_experience_non_overlapping(work_experience_items: List[Any]) -> None:
    """Validates that:
    1. For each work experience entry, start_date <= end_date.
    2. No two work experience entries overlap in their date ranges.
    Raises ValueError with a descriptive message if an overlap or invalid range is detected.
    """
    if not work_experience_items:
        return

    intervals = []
    now_ms = time.time() * 1000.0

    for idx, raw_item in enumerate(work_experience_items):
        item = raw_item
        if not isinstance(item, dict):
            item = item.model_dump() if hasattr(item, "model_dump") else dict(item)

        start = parse_date_to_ms(item.get("start_date"))
        is_curr = bool(item.get("is_currently_work_here"))
        end = now_ms if is_curr else parse_date_to_ms(item.get("end_date"))
        title = item.get("job_title") or item.get("title") or item.get("company_name") or f"Item #{idx+1}"

        if start is not None and end is not None:
            if start > end:
                raise ValueError(f"Work experience start date cannot be after end date for '{title}'.")
            intervals.append((start, end, title))

    if len(intervals) <= 1:
        return

    # Sort intervals by start timestamp, then end timestamp
    intervals.sort(key=lambda x: (x[0], x[1]))

    max_end = intervals[0][1]
    max_title = intervals[0][2]

    for i in range(1, len(intervals)):
        start, end, title = intervals[i]
        # Strictly overlapping if start < max_end
        if start < max_end:
            raise ValueError(
                f"Work experience date ranges cannot overlap: '{max_title}' overlaps with '{title}'."
            )
        if end > max_end:
            max_end = end
            max_title = title


def calculate_candidate_experience_years(work_experience_items: List[Any]) -> float:
    """Calculates total non-overlapping candidate work experience in years.
    Handles start_date and end_date in milliseconds (or string dates).
    Merges any overlapping intervals so time is never double-counted.
    Returns a float rounded to 1 decimal place (e.g. 3.2).
    """
    if not work_experience_items:
        return 0.0

    intervals = []
    now_ms = time.time() * 1000.0

    for item in work_experience_items:
        if not isinstance(item, dict):
            item = item.model_dump() if hasattr(item, "model_dump") else dict(item)

        start_ms = parse_date_to_ms(item.get("start_date"))
        if start_ms is None:
            continue

        is_current = bool(item.get("is_currently_work_here"))
        raw_end = item.get("end_date")
        if is_current or (isinstance(raw_end, str) and raw_end.strip().lower() in ("present", "current", "now", "ongoing")):
            end_ms = now_ms
        else:
            end_ms = parse_date_to_ms(raw_end)
            if end_ms is None:
                end_ms = start_ms

        if end_ms < start_ms:
            end_ms = start_ms

        intervals.append([start_ms, end_ms])

    if not intervals:
        return 0.0

    # Sort intervals by start time
    intervals.sort(key=lambda x: x[0])

    # Merge overlapping intervals
    merged = [intervals[0]]
    for cur in intervals[1:]:
        prev = merged[-1]
        if cur[0] <= prev[1]:
            prev[1] = max(prev[1], cur[1])
        else:
            merged.append(cur)

    total_ms = sum(inv[1] - inv[0] for inv in merged)
    MS_PER_YEAR = 1000.0 * 60 * 60 * 24 * 365.25
    years = total_ms / MS_PER_YEAR
    return round(max(0.0, years), 1)


SKILL_TO_CATEGORY_MAP = {
    # 1. Programming Languages
    "python": "Programming Languages", "javascript": "Programming Languages",
    "typescript": "Programming Languages", "java": "Programming Languages",
    "c++": "Programming Languages", "c#": "Programming Languages", "c": "Programming Languages",
    "go": "Programming Languages", "golang": "Programming Languages", "rust": "Programming Languages",
    "php": "Programming Languages", "ruby": "Programming Languages", "sql": "Programming Languages",
    "pl/sql": "Programming Languages", "swift": "Programming Languages", "kotlin": "Programming Languages",
    "scala": "Programming Languages", "r": "Programming Languages", "dart": "Programming Languages",
    "bash": "Programming Languages", "shell": "Programming Languages",

    # 2. Frameworks & Libraries
    "django": "Frameworks & Libraries", "drf": "Frameworks & Libraries",
    "django rest framework": "Frameworks & Libraries", "django-rest-framework": "Frameworks & Libraries",
    "fastapi": "Frameworks & Libraries", "flask": "Frameworks & Libraries",
    "spring boot": "Frameworks & Libraries", "spring": "Frameworks & Libraries",
    "express": "Frameworks & Libraries", "express.js": "Frameworks & Libraries",
    "node.js": "Frameworks & Libraries", "nodejs": "Frameworks & Libraries",
    "nest.js": "Frameworks & Libraries", "nestjs": "Frameworks & Libraries",
    "sqlalchemy": "Frameworks & Libraries", "django orm": "Frameworks & Libraries",
    "hibernate": "Frameworks & Libraries", "prisma": "Frameworks & Libraries",
    "ruby on rails": "Frameworks & Libraries", "rails": "Frameworks & Libraries",
    "asp.net": "Frameworks & Libraries", "microservices": "Frameworks & Libraries",

    # 3. Databases
    "postgresql": "Databases", "postgres": "Databases", "mysql": "Databases",
    "mongodb": "Databases", "mongo": "Databases", "redis": "Databases", "sqlite": "Databases",
    "elasticsearch": "Databases", "cassandra": "Databases", "dynamodb": "Databases",
    "mariadb": "Databases", "oracle": "Databases", "neo4j": "Databases",

    # 4. Tools & Technologies
    "git": "Tools & Technologies", "github": "Tools & Technologies", "gitlab": "Tools & Technologies",
    "git & github": "Tools & Technologies", "postman": "Tools & Technologies", "jira": "Tools & Technologies",
    "jira webhooks": "Tools & Technologies", "swagger": "Tools & Technologies", "vite": "Tools & Technologies",
    "webpack": "Tools & Technologies", "kafka": "Tools & Technologies", "rabbitmq": "Tools & Technologies",
    "celery": "Tools & Technologies", "npm": "Tools & Technologies", "yarn": "Tools & Technologies",
    "pnpm": "Tools & Technologies",

    # 5. Cloud & DevOps
    "aws": "Cloud & DevOps", "azure": "Cloud & DevOps", "gcp": "Cloud & DevOps",
    "google cloud": "Cloud & DevOps", "docker": "Cloud & DevOps", "kubernetes": "Cloud & DevOps",
    "k8s": "Cloud & DevOps", "ci/cd": "Cloud & DevOps", "cicd": "Cloud & DevOps",
    "terraform": "Cloud & DevOps", "ansible": "Cloud & DevOps", "jenkins": "Cloud & DevOps",
    "nginx": "Cloud & DevOps", "cloudformation": "Cloud & DevOps",

    # 6. Web Development
    "react": "Web Development", "react.js": "Web Development", "reactjs": "Web Development",
    "next.js": "Web Development", "nextjs": "Web Development", "vue": "Web Development",
    "vue.js": "Web Development", "angular": "Web Development", "tailwind": "Web Development",
    "tailwind css": "Web Development", "bootstrap": "Web Development", "html": "Web Development",
    "html5": "Web Development", "css": "Web Development", "css3": "Web Development",
    "restful apis": "Web Development", "rest apis": "Web Development", "rest api": "Web Development",
    "graphql": "Web Development", "websockets": "Web Development", "redux": "Web Development",

    # 7. AI & Machine Learning
    "langchain": "AI & Machine Learning", "langgraph": "AI & Machine Learning",
    "rag": "AI & Machine Learning", "rag systems": "AI & Machine Learning",
    "ai orchestrator": "AI & Machine Learning", "ai orchestration": "AI & Machine Learning",
    "openai": "AI & Machine Learning", "openai apis": "AI & Machine Learning",
    "gemini": "AI & Machine Learning", "machine learning": "AI & Machine Learning",
    "deep learning": "AI & Machine Learning", "pytorch": "AI & Machine Learning",
    "tensorflow": "AI & Machine Learning", "vector search": "AI & Machine Learning",
    "pinecone": "AI & Machine Learning", "chroma": "AI & Machine Learning",
    "chroma db": "AI & Machine Learning", "llm": "AI & Machine Learning", "llms": "AI & Machine Learning",

    # 8. Data Analysis & Visualization
    "pandas": "Data Analysis & Visualization", "numpy": "Data Analysis & Visualization",
    "tableau": "Data Analysis & Visualization", "power bi": "Data Analysis & Visualization",
    "matplotlib": "Data Analysis & Visualization", "seaborn": "Data Analysis & Visualization",
    "excel": "Data Analysis & Visualization", "spark": "Data Analysis & Visualization",
    "apache spark": "Data Analysis & Visualization", "databricks": "Data Analysis & Visualization",

    # 9. Testing & QA
    "pytest": "Testing & QA", "selenium": "Testing & QA", "appium": "Testing & QA",
    "cucumber": "Testing & QA", "automated testing": "Testing & QA", "unit testing": "Testing & QA",
    "jest": "Testing & QA", "cypress": "Testing & QA", "playwright": "Testing & QA",

    # 10. Operating Systems
    "linux": "Operating Systems", "ubuntu": "Operating Systems", "debian": "Operating Systems",
    "centos": "Operating Systems", "redhat": "Operating Systems", "windows": "Operating Systems",
    "macos": "Operating Systems", "unix": "Operating Systems",
}


def structure_skills_into_categories(
    skills_data: Any,
    existing_categorized: Optional[Dict[str, List[str]]] = None,
    include_empty: bool = False,
) -> Dict[str, List[str]]:
    """Structures any skills data (dict, list of category objects, or list of strings)
    into the 10 standard skill categories. Preserves candidate's pre-assigned categories when present.
    """
    result: Dict[str, List[str]] = {cat: [] for cat in ORDERED_SKILL_CATEGORIES}

    def add_skill(cat_name: str, skill_val: str):
        cleaned = re.sub(r"\s*\(.*?\)", "", str(skill_val)).strip()
        if not cleaned:
            return
        target_cat = None
        for c in ORDERED_SKILL_CATEGORIES:
            if c.lower() == cat_name.strip().lower():
                target_cat = c
                break
        if not target_cat:
            target_cat = cat_name.strip()
            if target_cat not in result:
                result[target_cat] = []

        if cleaned.lower() not in [s.lower() for s in result[target_cat]]:
            result[target_cat].append(cleaned)

    # 1. If existing categorized skills provided, seed with them
    if isinstance(existing_categorized, dict):
        for c_name, c_skills in existing_categorized.items():
            if isinstance(c_skills, list):
                for s in c_skills:
                    add_skill(c_name, s)

    # 2. Process incoming skills_data
    if isinstance(skills_data, dict):
        if "skills" in skills_data and len(skills_data) <= 3:
            skills_data = skills_data["skills"]

        if isinstance(skills_data, dict):
            for c_name, c_skills in skills_data.items():
                if isinstance(c_skills, list):
                    for s in c_skills:
                        add_skill(c_name, s)
        elif isinstance(skills_data, list):
            for item in skills_data:
                if isinstance(item, dict):
                    c_name = item.get("category") or item.get("name") or "Tools & Technologies"
                    for s in (item.get("skills") or item.get("items") or []):
                        add_skill(c_name, s)
                elif item:
                    cat = SKILL_TO_CATEGORY_MAP.get(str(item).strip().lower(), "Tools & Technologies")
                    add_skill(cat, item)

    elif isinstance(skills_data, list):
        for item in skills_data:
            if isinstance(item, dict):
                c_name = item.get("category") or item.get("name") or "Tools & Technologies"
                for s in (item.get("skills") or item.get("items") or []):
                    add_skill(c_name, s)
            elif item:
                s_clean = str(item).strip()
                s_lower = s_clean.lower()
                cat = SKILL_TO_CATEGORY_MAP.get(s_lower)
                if not cat:
                    for k_map, v_cat in SKILL_TO_CATEGORY_MAP.items():
                        if k_map in s_lower or s_lower in k_map:
                            cat = v_cat
                            break
                if not cat:
                    cat = "Tools & Technologies"
                add_skill(cat, s_clean)

    # Filter out empty categories (unless include_empty is True) and return in standard 10-category order
    final_dict: Dict[str, List[str]] = {}
    for cat in ORDERED_SKILL_CATEGORIES:
        if cat in result:
            if result[cat] or include_empty:
                final_dict[cat] = result[cat]
    for cat, items in result.items():
        if cat not in ORDERED_SKILL_CATEGORIES:
            if items or include_empty:
                final_dict[cat] = items

    return final_dict
