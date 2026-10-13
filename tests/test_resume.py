import io


def test_resume_skills_flow(client, test_user):
    headers = test_user["headers"]

    # 1. Save Skills
    skills_payload = {"skills": ["Python", "FastAPI", "PostgreSQL"]}
    save_resp = client.post("/api/v1/resume/save-skills", json=skills_payload, headers=headers)
    assert save_resp.status_code == 200
    save_data = save_resp.json()["data"]
    assert "Python" in save_data["skills"]

    # 2. Update Skills (previously threw ValueError: too many values to unpack)
    update_payload = {"skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"]}
    update_resp = client.patch("/api/v1/resume/update-skills", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    update_data = update_resp.json()["data"]
    assert len(update_data["skills"]) == 5
    assert "Docker" in update_data["skills"]


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

    save_resp = client.post("/api/v1/resume/save-personal-info", json=payload, headers=headers)
    assert save_resp.status_code == 200

    update_payload = {"city": "Oakland"}
    update_resp = client.patch("/api/v1/resume/update-personal-info", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["city"] == "Oakland"


def test_resume_professional_summary_flow(client, test_user):
    headers = test_user["headers"]

    summary_payload = {"summary": "Experienced Full Stack Software Engineer."}
    save_resp = client.post("/api/v1/resume/save-professional-summary", json=summary_payload, headers=headers)
    assert save_resp.status_code == 200

    update_payload = {"summary": "Senior Staff Software Engineer."}
    update_resp = client.patch("/api/v1/resume/update-professional-summary", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["summary"] == "Senior Staff Software Engineer."


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
