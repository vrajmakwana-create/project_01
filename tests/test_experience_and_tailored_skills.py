import pytest
import time
from app.common.utils import (
    parse_date_to_ms,
    validate_work_experience_non_overlapping,
    calculate_candidate_experience_years,
    structure_skills_into_categories,
    ORDERED_SKILL_CATEGORIES,
)
from app.schema.resume import WorkExperienceSchema, WorkExperienceItemSchema
from app.services.pdf_generator_service import pdf_generator_service
from app.services.gemini_service import gemini_service


def test_parse_date_to_ms():
    # Millisecond number
    ms_val = 1711929600000
    assert parse_date_to_ms(ms_val) == 1711929600000.0

    # Millisecond string
    assert parse_date_to_ms("1711929600000") == 1711929600000.0

    # Epoch seconds
    sec_val = 1711929600
    assert parse_date_to_ms(sec_val) == 1711929600000.0

    # Date string YYYY-MM
    ms_date = parse_date_to_ms("2024-01")
    assert ms_date is not None
    assert ms_date > 0

    # Present / Current string
    pres_ms = parse_date_to_ms("Present")
    assert pres_ms is not None
    assert abs(pres_ms - (time.time() * 1000.0)) < 5000.0

    # Empty / None
    assert parse_date_to_ms(None) is None
    assert parse_date_to_ms("") is None


def test_work_experience_validation_success():
    # Job 1: 2022-01-01 to 2022-12-31 (1640995200000 to 1672444800000)
    # Job 2: 2023-01-01 to 2023-12-31 (1672531200000 to 1703980800000)
    items = [
        {"title": "Dev 1", "company": "A", "start_date": 1640995200000, "end_date": 1672444800000},
        {"title": "Dev 2", "company": "B", "start_date": 1672531200000, "end_date": 1703980800000},
    ]
    # Should not raise
    validate_work_experience_non_overlapping(items)

    schema = WorkExperienceSchema(work_experience=items)
    assert len(schema.work_experience) == 2
    # Verify milliseconds preserved as raw values
    assert schema.work_experience[0].start_date == 1640995200000
    assert schema.work_experience[0].end_date == 1672444800000
    # Verify individual item experience
    assert schema.work_experience[0].experience_years == 1.0
    assert schema.work_experience[1].experience_years == 1.0
    # Verify TOTAL experience across all items
    assert schema.total_experience_years == 2.0
    assert schema.candidate_experience_years == 2.0


def test_multiple_work_experiences_total_experience_sum():
    # Job 1: 2019-01-01 to 2019-12-31 (~1.0 year)
    # Job 2: 2020-01-01 to 2021-06-30 (~1.5 years)
    # Job 3: 2021-07-01 to 2023-06-30 (~2.0 years)
    # Total experience should be 1.0 + 1.5 + 2.0 = 4.5 years!
    items = [
        {"title": "Junior Dev", "company": "Company 1", "start_date": "2019-01-01", "end_date": "2019-12-31"},
        {"title": "Mid Dev", "company": "Company 2", "start_date": "2020-01-01", "end_date": "2021-06-30"},
        {"title": "Senior Dev", "company": "Company 3", "start_date": "2021-07-01", "end_date": "2023-06-30"},
    ]
    total_years = calculate_candidate_experience_years(items)
    assert total_years == 4.5

    schema = WorkExperienceSchema(work_experience=items)
    assert schema.total_experience_years == 4.5
    assert schema.candidate_experience_years == 4.5
    assert schema.work_experience[0].experience_years == 1.0
    assert schema.work_experience[1].experience_years == 1.5
    assert schema.work_experience[2].experience_years == 2.0


def test_work_experience_validation_overlapping_fails():
    # Job 1: 2023-01 to 2023-09
    # Job 2: 2023-06 to 2024-01 (overlaps with Job 1)
    items = [
        {"title": "Dev 1", "company": "A", "start_date": 1672531200000, "end_date": 1696118400000},
        {"title": "Dev 2", "company": "B", "start_date": 1685577600000, "end_date": 1704067200000},
    ]
    with pytest.raises(ValueError) as excinfo:
        validate_work_experience_non_overlapping(items)
    assert "overlap" in str(excinfo.value).lower()

    # Via Pydantic schema
    with pytest.raises(Exception):
        WorkExperienceSchema(work_experience=items)


def test_work_experience_validation_start_after_end_fails():
    items = [
        {"title": "Dev 1", "company": "A", "start_date": 1704067200000, "end_date": 1672531200000},
    ]
    with pytest.raises(ValueError) as excinfo:
        validate_work_experience_non_overlapping(items)
    assert "start date cannot be after end date" in str(excinfo.value).lower()


def test_structure_skills_into_categories():
    input_skills = {
        "Databases": ["PostgreSQL", "MongoDB"],
        "Testing & QA": ["Pytest"],
        "Cloud & DevOps": ["AWS", "Docker"],
        "Web Development": ["React", "RESTful APIs"],
        "Operating Systems": ["Linux", "Ubuntu"],
        "Tools & Technologies": ["Git & GitHub", "Postman"],
        "AI & Machine Learning": ["RAG Systems", "AI Orchestrator", "LangChain"],
        "Programming Languages": ["Python", "SQL"],
        "Frameworks & Libraries": ["Django", "DRF", "FastAPI"],
    }
    categorized = structure_skills_into_categories(input_skills)
    assert isinstance(categorized, dict)
    assert "Programming Languages" in categorized
    assert "Python" in categorized["Programming Languages"]
    assert "SQL" in categorized["Programming Languages"]
    assert "Data Analysis & Visualization" not in categorized  # empty category omitted

    # Test flat list
    flat_skills = ["Python", "PostgreSQL", "Docker", "Pytest", "Linux"]
    flat_categorized = structure_skills_into_categories(flat_skills)
    assert flat_categorized["Programming Languages"] == ["Python"]
    assert flat_categorized["Databases"] == ["PostgreSQL"]
    assert flat_categorized["Cloud & DevOps"] == ["Docker"]
    assert flat_categorized["Testing & QA"] == ["Pytest"]
    assert flat_categorized["Operating Systems"] == ["Linux"]


@pytest.mark.asyncio
async def test_fallback_analyze_jd_categorized_skills_and_exp():
    current_resume = {
        "professional_summary": "Experienced Python Engineer",
        "skills": {
            "Programming Languages": ["Python", "SQL"],
            "Databases": ["PostgreSQL"],
            "Cloud & DevOps": ["AWS"],
        },
        "work_experience": [
            {"title": "Python Dev", "company": "Acme", "start_date": 1640995200000, "end_date": 1704067200000}
        ],
        "candidate_experience_years": 2.0,
    }

    jd_text = """
    We are looking for a Senior Python Developer with 5+ years of experience.
    Must have hands-on experience in Python, FastAPI, Docker, and PostgreSQL.
    """

    res = gemini_service._fallback_analyze_jd(
        jd_text=jd_text,
        current_resume=current_resume,
        job_title="Senior Python Developer",
        company_name="TechCorp",
    )

    assert res["candidate_experience_years"] == 2.0
    assert res["jd_experience_years"] == 5.0
    assert isinstance(res["tailored_skills"], dict)
    # Check that tailored_skills is in categories dict format
    assert "Programming Languages" in res["tailored_skills"]
    assert "Python" in res["tailored_skills"]["Programming Languages"]


def test_pdf_generation_with_ms_dates_and_categories():
    personal_info = {
        "first_name": "Vraj",
        "last_name": "Makwana",
        "email": "vraj@yopmail.com",
        "phone": "7984562342",
        "linkedin": "linkedin.com/in/vraj6605",
    }
    summary = "Accomplished Software Engineer with extensive expertise in Python and distributed systems."
    skills = {
        "Programming Languages": ["Python", "SQL"],
        "Databases": ["PostgreSQL", "MongoDB"],
        "Cloud & DevOps": ["AWS", "Docker"],
    }
    work_experience = [
        {
            "job_title": "Python Developer",
            "company_name": "Zignuts Technolab",
            "start_date": 1672531200000,  # ~2023-01
            "end_date": 1719792000000,    # ~2024-07
            "responsibilities": [
                "Responsible for building scalable backend web application using FastAPI and Django.",
                "Designing RAG System and AI Orchestrator workflow."
            ]
        }
    ]
    projects = [
        {
            "project_name": "KreativeSpace",
            "description": "AI-powered platform designed to empower creativity and enhance productivity.",
            "url": "https://kreativespace.example.com",
            "start_date": "2024-01",
            "end_date": "Present",
            "responsibilities": ["Building scalable web application."]
        }
    ]
    education = [
        {
            "degree": "Bachelor of Engineering in Computer Engineering",
            "school_name": "GEC Modasa",
            "gpa": "7",
            "start_date": "2021",
            "end_date": "2025"
        }
    ]

    pdf_bytes = pdf_generator_service.generate_resume_pdf(
        personal_info=personal_info,
        summary=summary,
        skills=skills,
        work_experience=work_experience,
        projects=projects,
        education=education,
        target_role="PYTHON DEVELOPER",
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
