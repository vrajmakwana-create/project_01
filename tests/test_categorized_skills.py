import pytest
from app.schema.resume import SkillSchema, TECHNICAL_SKILL_CATEGORIES
from app.services.pdf_generator_service import pdf_generator_service, format_skills_dict, categorize_skills


def test_technical_skill_categories_list():
    assert len(TECHNICAL_SKILL_CATEGORIES) == 10
    expected = [
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
    assert TECHNICAL_SKILL_CATEGORIES == expected


def test_categorize_skills_with_dictionary():
    payload = {
        "Programming Languages": ["Python", "SQL"],
        "Frameworks & Libraries": ["Django", "FastAPI"],
        "Databases": ["PostgreSQL", "MongoDB"],
        "Tools & Technologies": ["Git", "Postman"],
        "Cloud & DevOps": ["AWS", "Docker"],
        "Web Development": ["React", "HTML5"],
        "AI & Machine Learning": ["LangChain", "RAG"],
        "Data Analysis & Visualization": ["Pandas", "NumPy"],
        "Testing & QA": ["Pytest", "Selenium"],
        "Operating Systems": ["Linux", "Ubuntu"],
    }
    categorized = format_skills_dict(payload)
    assert len(categorized) == 10
    assert categorized["Programming Languages"] == ["Python", "SQL"]
    assert categorized["Databases"] == ["PostgreSQL", "MongoDB"]
    assert categorized["Operating Systems"] == ["Linux", "Ubuntu"]


def test_categorize_skills_with_list_of_objects():
    payload = [
        {"category": "Programming Languages", "skills": ["Python", "Go"]},
        {"category": "Databases", "skills": ["PostgreSQL", "Redis"]},
    ]
    categorized = format_skills_dict(payload)
    assert "Programming Languages" in categorized
    assert categorized["Programming Languages"] == ["Python", "Go"]
    assert categorized["Databases"] == ["PostgreSQL", "Redis"]


def test_format_skills_with_user_exact_dictionary():
    user_payload = {
        "Databases": ["PostgreSQL", "MongoDB"],
        "Testing & QA": ["Pytest"],
        "Cloud & DevOps": ["AWS", "Docker"],
        "Web Development": ["React", "RESTful APIs"],
        "Operating Systems": ["Linux", "Ubuntu"],
        "Tools & Technologies": ["Git & GitHub", "Postman"],
        "AI & Machine Learning": ["RAG Systems", "AI Orchestrator", "LangChain"],
        "Programming Languages": ["Python", "SQL"],
        "Frameworks & Libraries": ["Django", "DRF", "FastAPI"]
    }
    result = format_skills_dict(user_payload)
    assert len(result) == 9
    assert result["Databases"] == ["PostgreSQL", "MongoDB"]
    assert result["Testing & QA"] == ["Pytest"]
    assert result["Cloud & DevOps"] == ["AWS", "Docker"]
    assert result["Web Development"] == ["React", "RESTful APIs"]
    assert result["Operating Systems"] == ["Linux", "Ubuntu"]
    assert result["Tools & Technologies"] == ["Git & GitHub", "Postman"]
    assert result["AI & Machine Learning"] == ["RAG Systems", "AI Orchestrator", "LangChain"]
    assert result["Programming Languages"] == ["Python", "SQL"]
    assert result["Frameworks & Libraries"] == ["Django", "DRF", "FastAPI"]
    assert "Data Analysis & Visualization" not in result


def test_save_and_update_categorized_skills_api(client, test_user):
    headers = test_user["headers"]

    # 1. Test POST /api/v1/resume/save-skills with categorized dictionary
    cat_payload = {
        "skills": {
            "Programming Languages": ["Python", "JavaScript", "SQL"],
            "Frameworks & Libraries": ["Django", "FastAPI", "Express"],
            "Databases": ["PostgreSQL", "MongoDB", "Redis"],
            "Tools & Technologies": ["Git & GitHub", "Postman"],
            "Cloud & DevOps": ["AWS", "Docker", "CI/CD"],
            "Web Development": ["React", "HTML5", "CSS3"],
            "AI & Machine Learning": ["RAG Systems", "LangChain"],
            "Data Analysis & Visualization": ["Pandas", "NumPy"],
            "Testing & QA": ["Pytest", "Unit Testing"],
            "Operating Systems": ["Linux", "Ubuntu"]
        }
    }

    save_resp = client.post("/api/v1/resume/save-skills", json=cat_payload, headers=headers)
    assert save_resp.status_code == 200
    res_data = save_resp.json()["data"]
    assert "skills" in res_data
    assert res_data["skills"]["Programming Languages"] == ["Python", "JavaScript", "SQL"]
    assert res_data["skills"]["Databases"] == ["PostgreSQL", "MongoDB", "Redis"]

    # 2. Test GET /api/v1/resume/skills
    get_resp = client.get("/api/v1/resume/skills", headers=headers)
    assert get_resp.status_code == 200
    get_data = get_resp.json()["data"]
    assert get_data["skills"]["Programming Languages"] == ["Python", "JavaScript", "SQL"]

    # 3. Test PATCH /api/v1/resume/update-skills
    update_payload = {
        "skills": {
            "Programming Languages": ["Python", "TypeScript", "SQL"],
            "Databases": ["PostgreSQL", "Redis"],
            "Cloud & DevOps": ["AWS", "Kubernetes"]
        }
    }
    update_resp = client.patch("/api/v1/resume/update-skills", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    upd_data = update_resp.json()["data"]
    assert upd_data["skills"]["Programming Languages"] == ["Python", "TypeScript", "SQL"]


def test_pdf_generation_with_categorized_skills():
    cat_skills = {
        "Programming Languages": ["Python", "SQL"],
        "Frameworks & Libraries": ["Django", "FastAPI"],
        "Databases": ["PostgreSQL", "MongoDB"],
        "Tools & Technologies": ["Git & GitHub", "Docker"],
        "Cloud & DevOps": ["AWS"],
        "Web Development": ["React", "HTML/CSS"],
        "AI & Machine Learning": ["RAG Systems", "LangChain"],
        "Data Analysis & Visualization": ["Pandas"],
        "Testing & QA": ["Pytest"],
        "Operating Systems": ["Linux"]
    }
    pdf_bytes = pdf_generator_service.generate_resume_pdf(
        personal_info={"first_name": "Vraj", "last_name": "Makwana"},
        skills=cat_skills,
    )
    assert len(pdf_bytes) > 1000
