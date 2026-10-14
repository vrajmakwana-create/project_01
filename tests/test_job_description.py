from app.db.models.job_description import JobDescription
from app.db.models.professional_summary_resume import ProfessionalSummaryResume
from app.db.models.skill_resume import SkillResume


def test_analyze_job_description_with_seniority_gap(client, test_user, db_session):
    headers = test_user["headers"]
    user_id = test_user["user"].id

    # 1. Setup candidate's original resume: Summary, Skills, and 2 Work Experiences (~3 years)
    client.post(
        "/api/v1/resume/save-professional-summary",
        json={"summary": "Mid-level backend engineer specializing in building Python and FastAPI REST APIs."},
        headers=headers,
    )
    client.post(
        "/api/v1/resume/save-skills",
        json={"skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]},
        headers=headers,
    )
    client.post(
        "/api/v1/resume/save-work-experience",
        json={
            "work_experience": [
                {
                    "job_title": "Backend Engineer",
                    "company_name": "Tech Corp",
                    "city": "Austin",
                    "state": "TX",
                    "country": "USA",
                    "location_type": "Remote",
                    "employment_type": "Full-time",
                    "is_currently_work_here": True,
                    "start_date": "2023-01-01",
                    "responsibilities": "Developed microservices with FastAPI and PostgreSQL",
                    "achievements": "Decreased latency by 30%",
                },
                {
                    "job_title": "Junior Developer",
                    "company_name": "Startup Inc",
                    "city": "Dallas",
                    "state": "TX",
                    "country": "USA",
                    "location_type": "Onsite",
                    "employment_type": "Full-time",
                    "is_currently_work_here": False,
                    "start_date": "2021-06-01",
                    "end_date": "2022-12-31",
                    "responsibilities": "Built backend endpoints in Python",
                    "achievements": "Implemented authentication",
                },
            ]
        },
        headers=headers,
    )

    # 2. Candidate analyzes a Senior JD that requires 7+ years of experience
    jd_payload = {
        "job_title": "Senior Cloud Infrastructure & Backend Architect",
        "company_name": "Enterprise Solutions",
        "job_description": (
            "We are seeking a Senior Backend Architect with 7+ years of extensive hands-on experience. "
            "The ideal candidate must excel in Python, FastAPI, PostgreSQL, Kubernetes, AWS, Terraform, and CI/CD. "
            "You will lead architectural decisions and containerized cloud migrations."
        ),
    }

    resp = client.post("/api/v1/job-description/analyze", json=jd_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    # Verify basic metadata
    assert data["id"] is not None
    assert data["job_title"] == "Senior Cloud Infrastructure & Backend Architect"
    assert data["company_name"] == "Enterprise Solutions"
    assert 0 <= data["match_score"] <= 100

    # Verify Experience & Seniority Gap Analysis
    exp_analysis = data["experience_analysis"]
    assert exp_analysis["jd_experience_years"] == 7.0
    assert exp_analysis["seniority_level_jd"] in ("Senior / Lead", "Senior")
    assert exp_analysis["experience_gap_verdict"] is not None
    assert "Seniority" in exp_analysis["experience_gap_verdict"] or "experience" in exp_analysis["experience_gap_verdict"].lower()

    # Verify Skills Difference (Matching vs Missing Skills)
    skills_analysis = data["skills_analysis"]
    matching = [s.lower() for s in skills_analysis["matching_skills"]]
    missing = [s.lower() for s in skills_analysis["missing_skills"]]

    # Candidate has Python, FastAPI, PostgreSQL, Docker
    assert "python" in matching
    assert "fastapi" in matching
    # JD demands Kubernetes, AWS, Terraform which candidate lacked
    assert "kubernetes" in missing or "aws" in missing or "terraform" in missing

    # Verify Interview Preparation Tips
    interview_prep = data["interview_preparation"]
    assert len(interview_prep) > 0
    first_tip = interview_prep[0]
    assert "skill" in first_tip
    assert len(first_tip.get("key_concepts_to_revise", [])) > 0
    assert len(first_tip.get("likely_interview_questions", [])) > 0

    # Verify Tailored Resume Content
    tailored = data["tailored_resume"]
    assert tailored["tailored_summary"] is not None
    assert len(tailored["tailored_summary"]) > 20
    assert len(tailored["tailored_skills"]) > 0
    for sk in tailored["tailored_skills"]:
        assert "(" not in sk and ")" not in sk
    assert tailored["professional_summary_id"] is not None
    assert tailored["skill_id"] is not None

    # 3. Verify Database Persistence in Relevant Tables
    db_session.expire_all()
    jd_row = db_session.query(JobDescription).filter(JobDescription.id == data["id"]).first()
    assert jd_row is not None
    assert jd_row.user_id == user_id
    assert jd_row.match_score == data["match_score"]

    # Verify that tailored summary was stored in professional_summary_resume with is_original = False
    tailored_summary_row = db_session.query(ProfessionalSummaryResume).filter(
        ProfessionalSummaryResume.id == tailored["professional_summary_id"]
    ).first()
    assert tailored_summary_row is not None
    assert tailored_summary_row.is_original is False
    assert tailored_summary_row.summary == tailored["tailored_summary"]

    # Verify that tailored skills were stored in skills_resume with is_original = False
    tailored_skill_row = db_session.query(SkillResume).filter(
        SkillResume.id == tailored["skill_id"]
    ).first()
    assert tailored_skill_row is not None
    assert tailored_skill_row.is_original is False
    assert tailored_skill_row.skills == tailored["tailored_skills"]

    # Verify candidate's original resume records remain untouched with is_original = True
    orig_summary = db_session.query(ProfessionalSummaryResume).filter(
        ProfessionalSummaryResume.user_id == user_id,
        ProfessionalSummaryResume.is_original == True,
    ).first()
    assert orig_summary is not None
    assert "Mid-level" in orig_summary.summary


def test_get_and_list_job_descriptions(client, test_user):
    headers = test_user["headers"]

    # 1. Analyze a JD
    analyze_resp = client.post(
        "/api/v1/job-description/analyze",
        json={
            "job_title": "Fullstack Developer",
            "company_name": "Acme",
            "job_description": "We need a Fullstack Developer proficient in React, Node.js, and MongoDB with 3 years of experience.",
        },
        headers=headers,
    )
    assert analyze_resp.status_code == 200
    jd_id = analyze_resp.json()["data"]["id"]

    # 2. Get by ID
    get_resp = client.get(f"/api/v1/job-description/{jd_id}", headers=headers)
    assert get_resp.status_code == 200
    get_data = get_resp.json()["data"]
    assert get_data["id"] == jd_id
    assert get_data["job_title"] == "Fullstack Developer"

    # 3. List
    list_resp = client.get("/api/v1/job-description/", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert len(items) >= 1
    assert any(item["id"] == jd_id for item in items)


def test_delete_job_description(client, test_user):
    headers = test_user["headers"]

    # Analyze JD
    analyze_resp = client.post(
        "/api/v1/job-description/analyze",
        json={
            "job_title": "DevOps Engineer",
            "job_description": "Seeking DevOps engineer with Docker, Kubernetes, CI/CD experience for 5 years.",
        },
        headers=headers,
    )
    assert analyze_resp.status_code == 200
    jd_id = analyze_resp.json()["data"]["id"]

    # Delete
    del_resp = client.delete(f"/api/v1/job-description/{jd_id}", headers=headers)
    assert del_resp.status_code == 200

    # Get after delete should be 404
    get_again = client.get(f"/api/v1/job-description/{jd_id}", headers=headers)
    assert get_again.status_code == 404


def test_unauthorized_job_description_endpoints(client):
    resp = client.post(
        "/api/v1/job-description/analyze",
        json={"job_description": "Valid job description text but missing authorization token."},
    )
    assert resp.status_code in (401, 403)
