import pytest
from app.db.models.job_description import JobDescription
from app.db.models.user import User


def test_generate_original_resume_on_onboarding_completion(client, test_user, db_session):
    """Verifies that completing the onboarding process (saving projects) automatically
    generates the original resume document, uploads it to Cloudinary (or local fallback),
    and persists the URL in the users table.
    """
    headers = test_user["headers"]
    user_id = str(test_user["user"].id)

    # 1. Step 1: Personal Info
    client.post(
        "/api/v1/resume/save-personal-info",
        json={
            "first_name": "Vraj",
            "last_name": "Makwana",
            "email": "vrajmakwana060605@gmail.com",
            "phone": "+91 7984691569",
            "address": "123 Tech Park",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "zip_code": "380015",
            "country": "India",
            "website": "https://vrajmakwana.dev",
            "github": "https://github.com/Vraj6605",
            "linkedin": "https://linkedin.com/in/vraj66",
        },
        headers=headers,
    )

    # 2. Step 2: Professional Summary
    client.post(
        "/api/v1/resume/save-professional-summary",
        json={
            "summary": "Performance-driven Python Developer with production experience in architecting scalable backend systems, robust RESTful APIs, and data layer integrations using Django, FastAPI, and SQLAlchemy."
        },
        headers=headers,
    )

    # 3. Step 3: Skills
    client.post(
        "/api/v1/resume/save-skills",
        json={
            "skills": [
                "Python", "JavaScript", "Java", "SQL",
                "Django", "FastAPI", "Node.js", "Express.js", "SQLAlchemy", "RESTful APIs",
                "PostgreSQL", "MySQL", "MongoDB", "LangChain", "LangGraph", "Docker", "Git", "Pytest"
            ]
        },
        headers=headers,
    )

    # 4. Step 4: Educational Info
    client.post(
        "/api/v1/resume/save-educational-info",
        json={
            "educations": [
                {
                    "degree": "Bachelor of Engineering (B.E.)",
                    "field_of_study": "Computer Engineering",
                    "school_name": "Gujarat Technological University (GTU)",
                    "gpa": "9.08 / 10.0",
                    "start_date": "2021",
                    "end_date": "2025",
                }
            ]
        },
        headers=headers,
    )

    # 5. Step 5: Work Experience
    client.post(
        "/api/v1/resume/save-work-experience",
        json={
            "work_experience": [
                {
                    "job_title": "Backend Python Developer",
                    "company_name": "Zignuts TechnoLab Pvt Ltd",
                    "city": "Ahmedabad",
                    "state": "Gujarat",
                    "country": "India",
                    "is_currently_work_here": True,
                    "start_date": "Jan 2025",
                    "responsibilities": "Engineered high-throughput backend applications and high-performance RESTful APIs.",
                    "achievements": "Decreased API latency and optimized database queries.",
                }
            ]
        },
        headers=headers,
    )

    # 6. Step 6 (Final Onboarding Step): Projects Info
    proj_resp = client.post(
        "/api/v1/resume/save-projects-info",
        json={
            "projects": [
                {
                    "name": "Blogify",
                    "description": "Full-Stack Blogging Platform",
                    "status": "MERN Stack",
                    "responsibilities": "Architected a scalable full-stack MERN blogging application enabling seamless content creation.",
                }
            ]
        },
        headers=headers,
    )
    assert proj_resp.status_code == 200
    res_data = proj_resp.json()["data"]

    # Verify resume_url is returned
    assert "resume_url" in res_data
    assert res_data["resume_url"] is not None

    # Verify user table in DB now has resume_url and onboarding_completed = True
    db_session.expire_all()
    user_row = db_session.query(User).filter(User.id == user_id).first()
    assert user_row is not None
    assert user_row.onboarding_completed is True
    assert user_row.resume_url is not None
    assert user_row.resume_url == res_data["resume_url"]


def test_generate_document_endpoint_on_demand(client, test_user):
    """Verifies that calling POST /api/v1/resume/generate-document generates and
    returns the updated resume URL.
    """
    headers = test_user["headers"]

    # Save summary and skills
    client.post(
        "/api/v1/resume/save-professional-summary",
        json={"summary": "Experienced Python Engineer."},
        headers=headers,
    )
    client.post(
        "/api/v1/resume/save-skills",
        json={"skills": ["Python", "FastAPI"]},
        headers=headers,
    )

    resp = client.post("/api/v1/resume/generate-document", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "resume_url" in data
    assert data["resume_url"] is not None


def test_tailored_resume_stored_in_job_description_table(client, test_user, db_session):
    """Verifies that analyzing a JD generates a tailored resume PDF, uploads to Cloudinary,
    and stores the resume_url directly in the job_descriptions table.
    """
    headers = test_user["headers"]
    user_id = str(test_user["user"].id)

    # Setup candidate original profile
    client.post(
        "/api/v1/resume/save-professional-summary",
        json={"summary": "Full Stack Python Developer proficient in FastAPI and Postgres."},
        headers=headers,
    )
    client.post(
        "/api/v1/resume/save-skills",
        json={"skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]},
        headers=headers,
    )

    jd_payload = {
        "job_title": "Senior Python Backend Engineer",
        "company_name": "Acme Cloud",
        "job_description": "We are seeking a Senior Python Backend Engineer with 5+ years experience in Python, FastAPI, Docker, and Kubernetes.",
    }

    analyze_resp = client.post("/api/v1/job-description/analyze", json=jd_payload, headers=headers)
    assert analyze_resp.status_code == 200
    res_data = analyze_resp.json()["data"]

    # Verify resume_url in API response
    assert "resume_url" in res_data
    assert res_data["resume_url"] is not None
    assert res_data["tailored_resume"]["resume_url"] is not None

    jd_id = res_data["id"]

    # Verify directly in PostgreSQL job_descriptions table
    db_session.expire_all()
    jd_row = db_session.query(JobDescription).filter(JobDescription.id == jd_id).first()
    assert jd_row is not None
    assert jd_row.resume_url is not None
    assert jd_row.resume_url == res_data["resume_url"]

    # Verify GET /job-description/{id} returns resume_url
    get_resp = client.get(f"/api/v1/job-description/{jd_id}", headers=headers)
    assert get_resp.status_code == 200
    get_data = get_resp.json()["data"]
    assert get_data["resume_url"] == jd_row.resume_url



def test_download_resume_endpoint(client, test_user):
    headers = test_user['headers']
    client.post('/api/v1/resume/save-professional-summary', json={'summary': 'Experienced Engineer'}, headers=headers)
    resp = client.get('/api/v1/resume/download', headers=headers, follow_redirects=False)
    # Should either redirect to Cloudinary HTTPS URL (307/302) or return 200 with PDF content
    assert resp.status_code in (200, 302, 307)
