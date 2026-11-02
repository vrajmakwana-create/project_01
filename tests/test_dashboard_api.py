import pytest
from unittest.mock import patch
from starlette.testclient import TestClient


def test_dashboard_endpoint_empty_profile(client: TestClient, test_user: dict):
    headers = test_user["headers"]

    resp = client.get("/api/v1/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    # KPIs check
    assert "kpis" in data
    assert data["kpis"]["tailored_applications_count"] == 0
    assert data["kpis"]["total_experience_years"] == 0.0
    assert 0 <= data["kpis"]["overall_resume_score"] <= 100
    assert 0 <= data["kpis"]["ats_parsing_rate"] <= 100

    # Primary resume check
    assert "primary_resume" in data
    assert data["primary_resume"]["completeness_score"] >= 0
    assert "sections_status" in data["primary_resume"]

    # Skills analytics check
    assert "skills_analytics" in data
    assert data["skills_analytics"]["total_skills_count"] == 0

    # Recommendations
    assert "actionable_recommendations" in data
    assert isinstance(data["actionable_recommendations"], list)


def test_dashboard_endpoint_full_profile(client: TestClient, test_user: dict):
    headers = test_user["headers"]

    # 1. Save Personal Info (with all required fields)
    p_resp = client.post(
        "/api/v1/resume/save-personal-info",
        json={
            "first_name": "Senior",
            "last_name": "Designer",
            "email": "designer@example.com",
            "phone": "+1 555-0199",
            "address": "100 Market Street",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
            "country": "USA",
            "github": "https://github.com/designer",
            "linkedin": "https://linkedin.com/in/designer",
            "website": "https://designer.portfolio.com",
        },
        headers=headers,
    )
    assert p_resp.status_code == 200

    # 2. Save Summary
    s_resp = client.post(
        "/api/v1/resume/save-professional-summary",
        json={
            "summary": "Creative and analytical Senior Product Designer with 5+ years of experience leading cross-functional teams, architecting scalable design systems, and delivering user-centric mobile and web experiences."
        },
        headers=headers,
    )
    assert s_resp.status_code == 200

    # 3. Save Skills
    sk_resp = client.post(
        "/api/v1/resume/save-skills",
        json={
            "skills": [
                "Figma", "UI/UX Design", "Wireframing", "Prototyping",
                "React", "HTML", "CSS", "Design Systems", "User Research", "Python"
            ]
        },
        headers=headers,
    )
    assert sk_resp.status_code == 200

    # 4. Save Education
    edu_resp = client.post(
        "/api/v1/resume/save-educational-info",
        json={
            "educations": [
                {
                    "degree": "Bachelor of Fine Arts in Interaction Design",
                    "school_name": "Design Academy",
                    "start_date": "2015-09",
                    "end_date": "2019-06",
                }
            ]
        },
        headers=headers,
    )
    assert edu_resp.status_code == 200

    # 5. Save Work Experience (2 distinct roles)
    w_resp = client.post(
        "/api/v1/resume/save-work-experience",
        json={
            "work_experience": [
                {
                    "job_title": "Senior Product Designer",
                    "company_name": "Design Studios Inc",
                    "start_date": 1625097600000,  # 2021-07
                    "end_date": 1688169600000,    # 2023-07 (~2.0 years)
                    "responsibilities": [
                        "Architected scalable design systems across 3 core platforms.",
                        "Led and managed a team of 4 product designers, reducing design debt by 40%."
                    ],
                },
                {
                    "job_title": "Product Designer",
                    "company_name": "Tech Corp",
                    "start_date": 1577836800000,  # 2020-01
                    "end_date": 1625011200000,    # 2021-06 (~1.5 years)
                    "responsibilities": [
                        "Built high-fidelity interactive prototypes and conducted weekly user research sessions.",
                    ],
                }
            ]
        },
        headers=headers,
    )
    assert w_resp.status_code == 200

    # 6. Save Projects
    pr_resp = client.post(
        "/api/v1/resume/save-projects-info",
        json={
            "projects": [
                {
                    "name": "DesignSystem Pro",
                    "description": "Open-source comprehensive multi-brand component library for modern web apps.",
                    "url": "https://github.com/designer/designsystem",
                }
            ]
        },
        headers=headers,
    )
    assert pr_resp.status_code == 200

    # 7. Analyze a Job Description (mocking gemini call to ensure fast, deterministic testing)
    mock_analysis = {
        "job_title": "Senior Product Designer",
        "company_name": "Acme Innovations",
        "match_score": 85,
        "match_rationale": "Strong alignment in product design and design systems.",
        "jd_experience_years": 4.0,
        "candidate_experience_years": 3.5,
        "seniority_level_jd": "Senior / Lead",
        "seniority_level_candidate": "Mid-Level",
        "experience_gap_verdict": "Candidate experience aligns well with target role.",
        "extracted_jd_skills": ["Figma", "Design Systems", "Prototyping", "User Research"],
        "matching_skills": ["Figma", "Design Systems", "Prototyping"],
        "missing_skills": ["User Research"],
        "interview_preparation_tips": [
            {
                "skill": "User Research",
                "priority": "High",
                "why_important": "Core requirement for the role.",
                "key_concepts_to_revise": ["Quantitative and qualitative methods"],
                "likely_interview_questions": ["How do you conduct user testing?"]
            }
        ],
        "tailored_summary": "Experienced Senior Product Designer skilled in Figma...",
        "tailored_skills": {
            "Tools & Technologies": ["Figma", "Wireframing"],
            "Web Development": ["Design Systems"]
        }
    }

    with patch("app.services.gemini_service.gemini_service.analyze_jd_and_tailor_resume", return_value=mock_analysis):
        jd_resp = client.post(
            "/api/v1/job-description/analyze",
            json={
                "job_title": "Senior Product Designer",
                "company_name": "Acme Innovations",
                "job_description": "We are seeking a Senior Product Designer with 4+ years experience skilled in Figma, Design Systems, and Prototyping.",
            },
            headers=headers,
        )
        assert jd_resp.status_code == 200

    # 8. Query Dashboard API
    dashboard_resp = client.get("/api/v1/dashboard", headers=headers)
    assert dashboard_resp.status_code == 200
    res_data = dashboard_resp.json()["data"]

    # Verify KPIs
    kpis = res_data["kpis"]
    assert kpis["overall_resume_score"] >= 80
    assert kpis["ats_parsing_rate"] >= 85
    assert kpis["tailored_applications_count"] == 1
    assert kpis["average_match_score"] == 85.0
    assert 3.4 <= kpis["total_experience_years"] <= 3.6

    # Verify Primary Resume
    primary = res_data["primary_resume"]
    assert primary["target_role"] == "Senior Product Designer"
    assert primary["candidate_name"] == "Senior Designer"
    assert primary["completeness_score"] == 100
    assert primary["sections_status"]["personal_info"] is True
    assert primary["sections_status"]["professional_summary"] is True
    assert primary["sections_status"]["skills"] is True
    assert primary["sections_status"]["education"] is True
    assert primary["sections_status"]["work_experience"] is True
    assert primary["sections_status"]["projects"] is True

    # Verify Skills Analytics
    skills_an = res_data["skills_analytics"]
    assert skills_an["total_skills_count"] >= 8
    assert skills_an["populated_categories_count"] >= 2
    assert isinstance(skills_an["skills_by_category"], dict)

    # Verify Tailored Applications Analytics
    apps_an = res_data["tailored_applications_analytics"]
    assert apps_an["total_count"] == 1
    assert len(apps_an["recent_tailored_applications"]) == 1
    recent_app = apps_an["recent_tailored_applications"][0]
    assert recent_app["job_title"] == "Senior Product Designer"
    assert recent_app["company_name"] == "Acme Innovations"
    assert recent_app["match_score"] == 85
