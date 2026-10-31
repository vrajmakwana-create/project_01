import html
import io
import re
from typing import Any, Dict, List, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.logger import get_logger

logger = get_logger(__name__)

# Color Palette precisely matched to the user's executive resume structure
PRIMARY_NAVY = colors.HexColor("#1A365D")   # Candidate name, section headings, divider lines
ACCENT_BLUE = colors.HexColor("#1F4E79")    # Subtitles, target roles, project badges
TEXT_DARK = colors.HexColor("#2D3748")      # Primary body and bullet text
TEXT_MUTED = colors.HexColor("#4A5568")     # Dates, institutions, and tech stacks
DIVIDER_COLOR = colors.HexColor("#1A365D")  # Header and section divider rules


def clean_text(val: Any) -> str:
    """Safely escapes HTML/XML special entities for ReportLab Paragraphs, replaces em/en-dashes with hyphens, and strips whitespace."""
    if val is None:
        return ""
    text = str(val).strip()
    text = text.replace("—", "-").replace("–", "-")
    return html.escape(text)


def format_date_str(val: Any) -> str:
    """Formats dates from YYYYMMDD (int/str), YYYY-MM-DD, YYYY-MM, or YYYY into a clean readable date string."""
    if not val:
        return ""
    val_str = str(val).strip()
    # YYYYMMDD (e.g. 20230101 -> 2023-01)
    if re.match(r"^\d{8}$", val_str):
        year = val_str[:4]
        month = int(val_str[4:6])
        return f"{year}-{month:02d}"
    # YYYY-MM-DD -> YYYY-MM
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val_str):
        return val_str[:7]
    return val_str


def format_bullets(raw_data: Any) -> List[str]:
    """Normalizes bullet points from list, string, or multiline text and capitalizes initial characters."""
    if not raw_data:
        return []
    raw_list: List[str] = []
    if isinstance(raw_data, list):
        for item in raw_data:
            if isinstance(item, str):
                for line in item.split("\n"):
                    clean_line = re.sub(r"^[\s•\-\*]+", "", line).strip()
                    if clean_line:
                        raw_list.append(clean_line)
            elif item:
                raw_list.append(str(item).strip())
    elif isinstance(raw_data, str):
        for line in raw_data.split("\n"):
            clean_line = re.sub(r"^[\s•\-\*]+", "", line).strip()
            if clean_line:
                raw_list.append(clean_line)
    else:
        raw_list = [str(raw_data).strip()]

    polished: List[str] = []
    for b in raw_list:
        if not b:
            continue
        # Capitalize leading character for polished presentation
        b = b[0].upper() + b[1:]
        polished.append(b)
    return polished


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


def format_skills_dict(skills_input: Any) -> Dict[str, List[str]]:
    """Formats directly stored categorized skills dictionary for PDF rendering.
    Filters out empty categories and preserves the clean 10-category executive order.
    No keyword-based auto-categorization guessing is performed.
    """
    if not skills_input:
        return {}

    # Handle wrapper dict e.g. {"skills": {...}}
    if isinstance(skills_input, dict) and "skills" in skills_input and len(skills_input) <= 3:
        skills_input = skills_input["skills"]

    # 1. Directly process the stored dictionary of categories -> lists
    if isinstance(skills_input, dict):
        result: Dict[str, List[str]] = {}
        # Render matching categories in standard executive order
        for cat in ORDERED_SKILL_CATEGORIES:
            for k, v in skills_input.items():
                if k.strip().lower() == cat.lower() and isinstance(v, list) and v:
                    cleaned_items = [str(s).strip() for s in v if str(s).strip()]
                    if cleaned_items:
                        result[cat] = cleaned_items
        # Include any custom categories specified by the user
        for k, v in skills_input.items():
            if not any(k.strip().lower() == c.lower() for c in ORDERED_SKILL_CATEGORIES):
                if isinstance(v, list) and v:
                    cleaned_items = [str(s).strip() for s in v if str(s).strip()]
                    if cleaned_items:
                        result[k.strip()] = cleaned_items
        return result

    # 2. List of category objects [{"category": "...", "skills": [...]}]
    if isinstance(skills_input, list) and skills_input and isinstance(skills_input[0], dict):
        cat_dict: Dict[str, List[str]] = {}
        for item in skills_input:
            cat_name = item.get("category") or item.get("name")
            skills_sub = item.get("skills") or item.get("items") or []
            if cat_name and isinstance(skills_sub, list):
                cat_dict[cat_name] = skills_sub
        return format_skills_dict(cat_dict)

    # 3. Fallback for flat list of strings
    if isinstance(skills_input, list) and skills_input:
        cleaned = [str(s).strip() for s in skills_input if str(s).strip()]
        return {"Technical Skills": cleaned} if cleaned else {}

    return {}


# Backward compatibility alias
categorize_skills = format_skills_dict


class PDFGeneratorService:
    """Generates standardized, publication-grade resume PDFs modeled exactly on the executive resume format."""

    def generate_resume_pdf(
        self,
        personal_info: Optional[Dict[str, Any]] = None,
        summary: Optional[Union[str, Dict[str, Any]]] = None,
        skills: Optional[Union[List[str], Dict[str, Any]]] = None,
        work_experience: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
        projects: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
        education: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
        target_role: Optional[str] = None,
    ) -> bytes:
        """Compiles resume data into a production-ready PDF binary."""
        personal_info = personal_info or {}

        # Normalize summary text
        summary_text = ""
        if isinstance(summary, str):
            summary_text = summary
        elif isinstance(summary, dict):
            summary_text = summary.get("summary", "")

        # Normalize skills data (supports dict, list of dicts, or list of strings)
        skills_data: Any = []
        if isinstance(skills, dict):
            if "skills" in skills and len(skills) <= 3:
                skills_data = skills.get("skills", [])
            else:
                skills_data = skills
        elif skills:
            skills_data = skills

        # Normalize work experience list
        work_list: List[Dict[str, Any]] = []
        if isinstance(work_experience, list):
            work_list = work_experience
        elif isinstance(work_experience, dict):
            work_list = work_experience.get("work_experience", [])

        # Normalize projects list
        proj_list: List[Dict[str, Any]] = []
        if isinstance(projects, list):
            proj_list = projects
        elif isinstance(projects, dict):
            proj_list = projects.get("projects", [])

        # Normalize education list
        edu_list: List[Dict[str, Any]] = []
        if isinstance(education, list):
            edu_list = education
        elif isinstance(education, dict):
            edu_list = education.get("educations", [])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Typography Styles
        name_style = ParagraphStyle(
            "CandidateName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=PRIMARY_NAVY,
            alignment=1,  # Center aligned
            spaceAfter=2,
        )
        role_style = ParagraphStyle(
            "CandidateRole",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=ACCENT_BLUE,
            alignment=1,  # Center aligned
            spaceAfter=4,
        )
        contact_style = ParagraphStyle(
            "ContactInfo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TEXT_DARK,
            alignment=1,  # Center aligned
            spaceAfter=6,
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=PRIMARY_NAVY,
            spaceBefore=7,
            spaceAfter=2,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "ResumeBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=TEXT_DARK,
            alignment=4,  # Justified
        )
        bullet_style = ParagraphStyle(
            "ResumeBullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
            leftIndent=24,
            firstLineIndent=-10,
            spaceAfter=2,
        )
        left_item_title = ParagraphStyle(
            "LeftItemTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#1A202C"),
            leftIndent=14,  # Tabbed under section headings
        )
        right_item_text = ParagraphStyle(
            "RightItemText",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=TEXT_MUTED,
            alignment=2,  # Right aligned
        )
        skills_category_style = ParagraphStyle(
            "SkillsCategory",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1A202C"),
            leftIndent=14,  # Indented / tabbed under TECHNICAL SKILLS
        )
        skills_list_style = ParagraphStyle(
            "SkillsList",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
        )
        tech_stack_style = ParagraphStyle(
            "TechStack",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=TEXT_MUTED,
            leftIndent=14,  # Tabbed under section headings
            spaceBefore=1,
            spaceAfter=2,
        )
        project_desc_style = ParagraphStyle(
            "ProjectDesc",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
            leftIndent=14,  # Tabbed under section headings
            spaceBefore=1,
            spaceAfter=2,
            alignment=4,  # Justified
        )
        edu_school_style = ParagraphStyle(
            "EduSchool",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
            leftIndent=14,  # Tabbed under section headings
        )

        story: List[Any] = []

        # ====================================================================
        # 1. HEADER (Name, Target Title, Contact Details)
        # ====================================================================
        first_name = clean_text(personal_info.get("first_name", ""))
        last_name = clean_text(personal_info.get("last_name", ""))
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = "CANDIDATE NAME"

        story.append(Paragraph(full_name.upper(), name_style))

        # Infer or use target role title
        display_role = target_role or personal_info.get("job_title")
        if not display_role and work_list:
            display_role = work_list[0].get("job_title") or work_list[0].get("title")
        if not display_role:
            display_role = "SOFTWARE DEVELOPER & BACKEND ENGINEER"

        story.append(Paragraph(clean_text(display_role).upper(), role_style))

        # Contact Bar
        contact_parts: List[str] = []
        phone = clean_text(personal_info.get("phone", ""))
        email = clean_text(personal_info.get("email", ""))
        linkedin = clean_text(personal_info.get("linkedin", ""))
        github = clean_text(personal_info.get("github", ""))
        website = clean_text(personal_info.get("website", ""))

        if phone:
            contact_parts.append(phone)
        if email:
            contact_parts.append(email)
        if linkedin:
            clean_li = linkedin.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            if clean_li.startswith("linkedin.com/"):
                pass
            elif clean_li.startswith("linkedin/"):
                clean_li = f"linkedin.com/{clean_li[9:]}"
            else:
                clean_li = f"linkedin.com/{clean_li.lstrip('/')}"
            contact_parts.append(clean_li)
        if github:
            clean_gh = github.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            if clean_gh.startswith("github.com/"):
                pass
            elif clean_gh.startswith("github/"):
                clean_gh = f"github.com/{clean_gh[7:]}"
            else:
                clean_gh = f"github.com/{clean_gh.lstrip('/')}"
            contact_parts.append(clean_gh)
        if website and not (linkedin and github):
            clean_web = website.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            contact_parts.append(clean_web)

        contact_line = " &nbsp;|&nbsp; ".join(contact_parts)
        if contact_line:
            story.append(Paragraph(contact_line, contact_style))

        # Horizontal Divider below header
        story.append(HRFlowable(width="100%", thickness=1, color=DIVIDER_COLOR, spaceAfter=7, spaceBefore=0))

        def add_section_header(title: str):
            story.append(Paragraph(title, section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.75, color=DIVIDER_COLOR, spaceAfter=5, spaceBefore=1))

        # ====================================================================
        # 2. PROFESSIONAL SUMMARY
        # ====================================================================
        if summary_text and summary_text.strip():
            add_section_header("PROFESSIONAL SUMMARY")
            story.append(Paragraph(clean_text(summary_text), body_style))
            story.append(Spacer(1, 5))

        # ====================================================================
        # 3. TECHNICAL SKILLS
        # ====================================================================
        if skills_data:
            add_section_header("TECHNICAL SKILLS")
            categorized = categorize_skills(skills_data)
            skill_rows = []
            for cat_name, cat_skills in categorized.items():
                skills_str = ", ".join(clean_text(s) for s in cat_skills if s)
                if skills_str:
                    col1 = Paragraph(clean_text(cat_name), skills_category_style)
                    col2 = Paragraph(skills_str, skills_list_style)
                    skill_rows.append([col1, col2])

            if skill_rows:
                table = Table(skill_rows, colWidths=[150, 390])
                table.setStyle(
                    TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ])
                )
                story.append(table)
                story.append(Spacer(1, 5))

        # ====================================================================
        # 4. PROFESSIONAL EXPERIENCE
        # ====================================================================
        if work_list:
            add_section_header("PROFESSIONAL EXPERIENCE")
            for item in work_list:
                title = clean_text(item.get("job_title") or item.get("title") or "")
                company = clean_text(item.get("company_name") or item.get("company") or "")
                start = format_date_str(item.get("start_date") or "")
                end = "Present" if item.get("is_currently_work_here") else format_date_str(item.get("end_date") or "")
                date_str = f"{start} - {end}".strip(" - ")

                left_heading = f"<b>{title}</b> &nbsp;-&nbsp; <i>{company}</i>" if company else f"<b>{title}</b>"
                header_table = Table(
                    [[Paragraph(left_heading, left_item_title), Paragraph(date_str, right_item_text)]],
                    colWidths=[380, 160],
                )
                header_table.setStyle(
                    TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ])
                )

                entry_story = [header_table]

                bullets = format_bullets(item.get("responsibilities")) + format_bullets(item.get("achievements"))
                for b in bullets:
                    entry_story.append(Paragraph(f"&bull;&nbsp;&nbsp;{clean_text(b)}", bullet_style))

                entry_story.append(Spacer(1, 4))
                # Keep header and first bullet together to avoid orphaned titles
                story.append(KeepTogether(entry_story[:2]) if len(entry_story) > 2 else KeepTogether(entry_story))
                for rem in entry_story[2:]:
                    story.append(rem)

        # ====================================================================
        # 5. KEY PROJECTS
        # ====================================================================
        if proj_list:
            add_section_header("KEY PROJECTS")
            for item in proj_list:
                p_name = clean_text(item.get("name") or "Project")
                p_url = (
                    item.get("url")
                    or item.get("project_url")
                    or item.get("link")
                    or item.get("live_url")
                    or item.get("github_url")
                )
                p_desc = clean_text(item.get("description") or "")

                title_parts = [f"<b>{p_name}</b>"]
                if p_url:
                    raw_url = str(p_url).strip()
                    href = raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}"
                    clean_display = raw_url.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
                    if len(clean_display) > 42:
                        clean_display = clean_display[:39] + "..."
                    clean_display = html.escape(clean_display)
                    title_parts.append(f'<font color="#1F4E79" size="8"><u><a href="{href}">[{clean_display}]</a></u></font>')

                # If description is a short phrase/tag (<= 35 chars without sentence terminator), keep inline
                short_desc = ""
                if p_desc and len(p_desc) <= 35 and not p_desc.endswith((".", "!", "?")):
                    short_desc = f" &nbsp;-&nbsp; <font color=\"#4A5568\" size=\"8.5\"><i>{p_desc}</i></font>"

                left_title_html = " &nbsp;|&nbsp; ".join(title_parts) + short_desc

                # Right column: Status, Category, or Dates
                status = clean_text(item.get("status") or "")
                category = clean_text(item.get("category") or "")
                start = format_date_str(item.get("start_date"))
                end = format_date_str(item.get("end_date"))
                date_str = f"{start} - {end}".strip(" - ") if (start or end) else ""

                right_items = []
                if category:
                    right_items.append(category)
                if status and status.lower() not in (category.lower(), ""):
                    right_items.append(status)
                if not right_items and date_str:
                    right_items.append(date_str)
                elif right_items and date_str and len(" | ".join(right_items)) < 15:
                    right_items.append(date_str)

                right_str = " &nbsp;|&nbsp; ".join(right_items) if right_items else ""

                header_table = Table(
                    [[Paragraph(left_title_html, left_item_title), Paragraph(right_str, right_item_text)]],
                    colWidths=[400, 140],
                )
                header_table.setStyle(
                    TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ])
                )

                p_story = [header_table]

                # Technologies line
                techs = item.get("technologies") or item.get("tech_stack")
                if techs:
                    if isinstance(techs, list):
                        tech_str = ", ".join(clean_text(t) for t in techs if t)
                    else:
                        tech_str = clean_text(techs)
                    if tech_str:
                        p_story.append(Paragraph(f"<b>Technologies:</b> {tech_str}", tech_stack_style))

                # Descriptive summary paragraph if description is comprehensive (> 35 chars or full sentence)
                if p_desc and (len(p_desc) > 35 or p_desc.endswith((".", "!", "?"))):
                    p_story.append(Paragraph(p_desc, project_desc_style))

                p_bullets = format_bullets(item.get("responsibilities")) + format_bullets(item.get("achievements"))
                for b in p_bullets:
                    p_story.append(Paragraph(f"&bull;&nbsp;&nbsp;{clean_text(b)}", bullet_style))

                p_story.append(Spacer(1, 4))
                story.append(KeepTogether(p_story[:2]) if len(p_story) > 2 else KeepTogether(p_story))
                for rem in p_story[2:]:
                    story.append(rem)

        # ====================================================================
        # 6. EDUCATION
        # ====================================================================
        if edu_list:
            add_section_header("EDUCATION")
            for item in edu_list:
                degree = clean_text(item.get("degree") or "")
                field = clean_text(item.get("field_of_study") or "")
                degree_text = f"<b>{degree}</b> in {field}" if field and field.lower() not in degree.lower() else f"<b>{degree}</b>"

                school = clean_text(item.get("school_name") or item.get("institution") or "")
                gpa = clean_text(item.get("gpa") or "")
                start = format_date_str(item.get("start_date") or "")
                end = format_date_str(item.get("end_date") or "")
                date_str = f"{start} - {end}".strip(" - ")

                right_parts = []
                if gpa:
                    if "cgpa" in gpa.lower() or "percentage" in gpa.lower():
                        right_parts.append(gpa)
                    elif "%" in gpa:
                        right_parts.append(f"Percentage: {gpa}")
                    else:
                        right_parts.append(f"CGPA: {gpa}")
                if date_str:
                    right_parts.append(date_str)
                right_str = " &nbsp;&nbsp; ".join(right_parts)

                col1_content = [Paragraph(degree_text, left_item_title)]
                if school:
                    col1_content.append(Paragraph(school, edu_school_style))

                edu_table = Table(
                    [[col1_content, Paragraph(right_str, right_item_text)]],
                    colWidths=[380, 160],
                )
                edu_table.setStyle(
                    TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ])
                )
                story.append(edu_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info(f"Generated standardized resume PDF (size={len(pdf_bytes)} bytes)")
        return pdf_bytes


pdf_generator_service = PDFGeneratorService()

