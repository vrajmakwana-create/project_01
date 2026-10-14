import io


def test_resume_skills_flow(client, test_user):
    headers = test_user["headers"]

    # 1. Save Skills
    skills_payload = {"skills": ["Python", "FastAPI", "PostgreSQL"]}
    save_resp = client.post("/api/v1/resume/save-skills", json=skills_payload, headers=headers)
    assert save_resp.status_code == 200
    save_data = save_resp.json()["data"]
    assert "Python" in save_data["skills"]

    # Duplicate save should fail
    dup_resp = client.post("/api/v1/resume/save-skills", json=skills_payload, headers=headers)
    assert dup_resp.status_code == 400

    # 2. Get Skills
    get_resp = client.get("/api/v1/resume/skills", headers=headers)
    assert get_resp.status_code == 200
    assert "Python" in get_resp.json()["data"]["skills"]

    # 3. Update Skills
    update_payload = {"skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"]}
    update_resp = client.patch("/api/v1/resume/update-skills", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    update_data = update_resp.json()["data"]
    assert len(update_data["skills"]) == 5
    assert "Docker" in update_data["skills"]

    # 4. Delete Skills
    del_resp = client.delete("/api/v1/resume/skills", headers=headers)
    assert del_resp.status_code == 200

    # 5. Get after delete should be 404
    get_after_del = client.get("/api/v1/resume/skills", headers=headers)
    assert get_after_del.status_code == 404


def test_resume_personal_info_flow(client, test_user):
    headers = test_user["headers"]

    payload = {
        "first_name": "Jane",
        "last_name": "Developer",
        "email": "jane@example.com",
        "phone": "+1234567890",
        "address": "123 Tech Street",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
        "country": "USA",
        "website": "https://janedev.com",
        "github": "https://github.com/janedev",
        "linkedin": "https://linkedin.com/in/janedev",
    }

    # 1. Save Personal Info
    save_resp = client.post("/api/v1/resume/save-personal-info", json=payload, headers=headers)
    assert save_resp.status_code == 200

    # Duplicate save should fail
    dup_resp = client.post("/api/v1/resume/save-personal-info", json=payload, headers=headers)
    assert dup_resp.status_code == 400

    # 2. Get Personal Info
    get_resp = client.get("/api/v1/resume/personal-info", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["email"] == "jane@example.com"

    # 3. Update Personal Info
    update_payload = {"city": "Oakland"}
    update_resp = client.patch("/api/v1/resume/update-personal-info", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["city"] == "Oakland"

    # 4. Delete Personal Info
    del_resp = client.delete("/api/v1/resume/personal-info", headers=headers)
    assert del_resp.status_code == 200

    # 5. Get after delete should be 404
    get_after_del = client.get("/api/v1/resume/personal-info", headers=headers)
    assert get_after_del.status_code == 404


def test_resume_professional_summary_flow(client, test_user):
    headers = test_user["headers"]

    summary_payload = {"summary": "Experienced Full Stack Software Engineer."}

    # 1. Save Professional Summary
    save_resp = client.post("/api/v1/resume/save-professional-summary", json=summary_payload, headers=headers)
    assert save_resp.status_code == 200

    # Duplicate save should fail
    dup_resp = client.post("/api/v1/resume/save-professional-summary", json=summary_payload, headers=headers)
    assert dup_resp.status_code == 400

    # 2. Get Professional Summary
    get_resp = client.get("/api/v1/resume/professional-summary", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["summary"] == "Experienced Full Stack Software Engineer."

    # 3. Update Professional Summary
    update_payload = {"summary": "Senior Staff Software Engineer."}
    update_resp = client.patch("/api/v1/resume/update-professional-summary", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["summary"] == "Senior Staff Software Engineer."

    # 4. Delete Professional Summary
    del_resp = client.delete("/api/v1/resume/professional-summary", headers=headers)
    assert del_resp.status_code == 200

    # 5. Get after delete should be 404
    get_after_del = client.get("/api/v1/resume/professional-summary", headers=headers)
    assert get_after_del.status_code == 404


def test_resume_educational_info_flow(client, test_user):
    headers = test_user["headers"]

    edu_payload = {
        "educations": [
            {
                "degree": "Bachelor of Technology in Computer Science",
                "school_name": "Stanford University",
                "start_date": "2018",
                "end_date": "2022",
                "gpa": "3.9",
                "field_of_study": "Computer Science",
            }
        ]
    }

    # 1. Save Educational Info
    save_resp = client.post("/api/v1/resume/save-educational-info", json=edu_payload, headers=headers)
    assert save_resp.status_code == 200
    save_data = save_resp.json()["data"]
    assert len(save_data["educations"]) == 1
    assert save_data["educations"][0]["degree"] == "Bachelor of Technology in Computer Science"
    assert save_data["educations"][0]["school_name"] == "Stanford University"

    # Duplicate save should fail with 400
    dup_resp = client.post("/api/v1/resume/save-educational-info", json=edu_payload, headers=headers)
    assert dup_resp.status_code == 400

    # 2. Get Educational Info
    get_resp = client.get("/api/v1/resume/educational-info", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["educations"][0]["degree"] == "Bachelor of Technology in Computer Science"

    # Test alias route /education
    get_alias = client.get("/api/v1/resume/education", headers=headers)
    assert get_alias.status_code == 200

    # 3. Update Educational Info
    update_payload = {
        "educations": [
            {
                "degree": "Bachelor of Technology in Computer Science",
                "school_name": "Stanford University",
                "start_date": "2018",
                "end_date": "2022",
                "gpa": "3.9",
            },
            {
                "degree": "Master of Science in Artificial Intelligence",
                "school_name": "MIT",
                "start_date": "2022",
                "end_date": "2024",
                "gpa": "4.0",
            },
        ]
    }
    update_resp = client.patch("/api/v1/resume/update-educational-info", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert len(update_resp.json()["data"]["educations"]) == 2

    # 4. Delete Educational Info
    del_resp = client.delete("/api/v1/resume/educational-info", headers=headers)
    assert del_resp.status_code == 200

    # 5. Get after delete should be 404
    get_after_del = client.get("/api/v1/resume/educational-info", headers=headers)
    assert get_after_del.status_code == 404


def test_resume_work_experience_flow(client, test_user):
    headers = test_user["headers"]

    work_payload = {
        "work_experience": [
            {
                "job_title": "Software Engineer",
                "company_name": "Google",
                "city": "Mountain View",
                "state": "CA",
                "country": "USA",
                "location_type": "Onsite",
                "employment_type": "Full-time",
                "is_currently_work_here": False,
                "start_date": "2021",
                "end_date": "2023",
                "responsibilities": "Building scalable backend services in Python and Go.",
                "achievements": "Improved latency by 35%.",
            }
        ]
    }

    # 1. Save Work Experience
    save_resp = client.post("/api/v1/resume/save-work-experience", json=work_payload, headers=headers)
    assert save_resp.status_code == 200
    save_data = save_resp.json()["data"]
    assert len(save_data["work_experience"]) == 1
    assert save_data["work_experience"][0]["job_title"] == "Software Engineer"
    assert save_data["work_experience"][0]["company_name"] == "Google"

    # Duplicate save should fail with 400
    dup_resp = client.post("/api/v1/resume/save-work-experience", json=work_payload, headers=headers)
    assert dup_resp.status_code == 400

    # 2. Get Work Experience
    get_resp = client.get("/api/v1/resume/work-experience", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["work_experience"][0]["company_name"] == "Google"

    # 3. Update Work Experience
    update_payload = {
        "work_experience": [
            {
                "job_title": "Senior Software Engineer",
                "company_name": "Google",
                "city": "Mountain View",
                "state": "CA",
                "country": "USA",
                "location_type": "Hybrid",
                "employment_type": "Full-time",
                "is_currently_work_here": True,
                "start_date": "2023",
                "end_date": None,
                "responsibilities": "Leading backend infrastructure architecture.",
                "achievements": "Scaled microservices to 10M daily active users.",
            }
        ]
    }
    update_resp = client.patch("/api/v1/resume/update-work-experience", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["work_experience"][0]["job_title"] == "Senior Software Engineer"

    # 4. Delete Work Experience
    del_resp = client.delete("/api/v1/resume/work-experience", headers=headers)
    assert del_resp.status_code == 200

    # 5. Get after delete should be 404
    get_after_del = client.get("/api/v1/resume/work-experience", headers=headers)
    assert get_after_del.status_code == 404


def test_resume_projects_info_flow(client, test_user):
    headers = test_user["headers"]

    projects_payload = {
        "projects": [
            {
                "name": "AI Resume Optimizer",
                "description": "An automated AI resume analysis and ATS scoring platform.",
                "url": "https://github.com/test/ai-resume",
                "start_date": 20230101,
                "end_date": 20230601,
                "status": "Completed",
                "responsibilities": "Developed backend APIs and AI scoring algorithms.",
                "achievements": "Reached 500+ active users in beta release.",
                "order": 1,
            }
        ]
    }

    # 1. Save Projects Info
    save_resp = client.post("/api/v1/resume/save-projects-info", json=projects_payload, headers=headers)
    assert save_resp.status_code == 200
    save_data = save_resp.json()["data"]
    assert len(save_data["projects"]) == 1
    assert save_data["projects"][0]["name"] == "AI Resume Optimizer"

    # Duplicate save should fail with 400
    dup_resp = client.post("/api/v1/resume/save-projects-info", json=projects_payload, headers=headers)
    assert dup_resp.status_code == 400

    # 2. Get Projects Info
    get_resp = client.get("/api/v1/resume/projects-info", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["projects"][0]["name"] == "AI Resume Optimizer"

    # Test alias route /project-info
    get_alias = client.get("/api/v1/resume/project-info", headers=headers)
    assert get_alias.status_code == 200

    # 3. Update Projects Info
    update_payload = {
        "projects": [
            {
                "name": "AI Resume Optimizer 2.0",
                "description": "Upgraded with real-time semantic analysis.",
                "url": "https://github.com/test/ai-resume-v2",
                "status": "In Progress",
                "responsibilities": "System architect and full stack dev.",
                "achievements": "Increased speed by 50%.",
                "order": 1,
            }
        ]
    }
    update_resp = client.patch("/api/v1/resume/update-projects-info", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["projects"][0]["name"] == "AI Resume Optimizer 2.0"

    # 4. Delete Projects Info
    del_resp = client.delete("/api/v1/resume/projects-info", headers=headers)
    assert del_resp.status_code == 200

    # 5. Get after delete should be 404
    get_after_del = client.get("/api/v1/resume/projects-info", headers=headers)
    assert get_after_del.status_code == 404


def test_resume_full_details_flow(client, test_user):
    headers = test_user["headers"]

    # Initially empty resume details
    initial_details = client.get("/api/v1/resume/details", headers=headers)
    assert initial_details.status_code == 200
    assert initial_details.json()["data"]["personal_info"] is None
    assert initial_details.json()["data"]["skills"] is None

    # Populate all sections
    client.post(
        "/api/v1/resume/save-personal-info",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "+1987654321",
            "address": "456 Market St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "website": "https://alicesmith.dev",
            "github": "https://github.com/alicesmith",
            "linkedin": "https://linkedin.com/in/alicesmith",
        },
        headers=headers,
    )

    client.post(
        "/api/v1/resume/save-professional-summary",
        json={"summary": "Accomplished software engineer with 6+ years of experience."},
        headers=headers,
    )

    client.post(
        "/api/v1/resume/save-skills",
        json={"skills": ["Python", "FastAPI", "React", "PostgreSQL"]},
        headers=headers,
    )

    client.post(
        "/api/v1/resume/save-educational-info",
        json={
            "educations": [
                {
                    "degree": "B.S. in Computer Science",
                    "school_name": "Columbia University",
                    "start_date": "2015",
                    "end_date": "2019",
                    "gpa": "3.85",
                }
            ]
        },
        headers=headers,
    )

    client.post(
        "/api/v1/resume/save-work-experience",
        json={
            "work_experience": [
                {
                    "job_title": "Lead Engineer",
                    "company_name": "Tech Corp",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "location_type": "Onsite",
                    "employment_type": "Full-time",
                    "is_currently_work_here": True,
                    "start_date": "2019",
                    "responsibilities": "Leading core product team.",
                    "achievements": "Grew revenue by 40%.",
                }
            ]
        },
        headers=headers,
    )

    client.post(
        "/api/v1/resume/save-projects-info",
        json={
            "projects": [
                {
                    "name": "Cloud Deployment Platform",
                    "description": "Internal PaaS for microservice deployment.",
                    "url": "https://github.com/alice/cloud-paas",
                    "status": "Active",
                    "responsibilities": "Lead developer",
                    "achievements": "Reduced deploy times to 2 minutes.",
                    "order": 1,
                }
            ]
        },
        headers=headers,
    )

    # Fetch full resume via /details
    full_resp = client.get("/api/v1/resume/details", headers=headers)
    assert full_resp.status_code == 200
    data = full_resp.json()["data"]

    assert data["personal_info"]["first_name"] == "Alice"
    assert data["professional_summary"]["summary"] == "Accomplished software engineer with 6+ years of experience."
    assert "FastAPI" in data["skills"]["skills"]
    assert len(data["educational_info"]["educations"]) == 1
    assert data["educational_info"]["educations"][0]["school_name"] == "Columbia University"
    assert len(data["work_experience"]["work_experience"]) == 1
    assert data["work_experience"]["work_experience"][0]["company_name"] == "Tech Corp"
    assert len(data["projects_info"]["projects"]) == 1
    assert data["projects_info"]["projects"][0]["name"] == "Cloud Deployment Platform"


def test_upload_resume_pdf(client, test_user):
    headers = test_user["headers"]

    fake_pdf = io.BytesIO(b"%PDF-1.4 sample pdf content for resume test")
    files = {"file": ("my_resume.pdf", fake_pdf, "application/pdf")}

    resp = client.post("/api/v1/resume/upload", files=files, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "filename" in data
    assert "file_path" in data


def test_upload_resume_invalid_type(client, test_user):
    headers = test_user["headers"]

    fake_txt = io.BytesIO(b"this is a text file")
    files = {"file": ("my_resume.txt", fake_txt, "text/plain")}

    resp = client.post("/api/v1/resume/upload", files=files, headers=headers)
    assert resp.status_code == 400
