import pytest
from unittest.mock import patch, AsyncMock
from app.core.message import SuccessMessage, ErrorMessage


def test_improve_summary_with_explicit_text_and_tone(client, test_user):
    """Tests improving a summary by providing draft summary text and specific tone."""
    headers = test_user["headers"]
    payload = {
        "summary": "Experienced Python backend engineer specialized in building scalable REST APIs with FastAPI, PostgreSQL, and Docker.",
        "tone": "executive",
    }

    response = client.post("/api/v1/resume/improve-summary", json=payload, headers=headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["msg"] == SuccessMessage.SUMMARY_IMPROVED_SUCCESSFULLY

    data = res_json["data"]
    assert "improved_summary" in data
    assert len(data["improved_summary"]) > 20
    assert data["original_summary"] == payload["summary"]
    assert "tone" in data
    assert isinstance(data.get("key_strengths"), list)
    assert isinstance(data.get("variations"), list)


def test_improve_summary_using_saved_db_summary(client, test_user):
    """Tests that if summary is omitted in request, it automatically uses the user's saved summary from DB."""
    headers = test_user["headers"]

    # First, save a professional summary in DB
    save_payload = {
        "summary": "Software engineer with 4 years background in distributed systems and cloud microservices."
    }
    save_resp = client.post("/api/v1/resume/save-professional-summary", json=save_payload, headers=headers)
    assert save_resp.status_code == 200

    # Call improve-summary without providing summary text
    improve_payload = {
        "tone": "technical"
    }
    improve_resp = client.post("/api/v1/resume/improve-summary", json=improve_payload, headers=headers)
    assert improve_resp.status_code == 200
    data = improve_resp.json()["data"]
    assert data["original_summary"] == save_payload["summary"]
    assert "improved_summary" in data
    assert len(data["improved_summary"]) > 20


def test_improve_summary_without_any_summary_returns_400(client, test_user):
    """Tests that if no summary is provided and none is saved in DB, 400 Bad Request is returned."""
    headers = test_user["headers"]
    payload = {
        "tone": "executive"
    }

    response = client.post("/api/v1/resume/improve-summary", json=payload, headers=headers)
    assert response.status_code == 400
    res_data = response.json()
    error_msg = res_data.get("msg") or res_data.get("detail")
    assert error_msg == ErrorMessage.SUMMARY_TEXT_REQUIRED


def test_improve_summary_unauthorized(client):
    """Tests that endpoint requires valid authentication."""
    response = client.post("/api/v1/resume/improve-summary", json={"summary": "Some summary text"})
    assert response.status_code in (401, 403)


def test_improve_summary_with_mocked_gemini(client, test_user):
    """Tests mocked Gemini AI generation to verify exact payload contract."""
    headers = test_user["headers"]
    mock_result = {
        "original_summary": "Junior developer with React experience.",
        "improved_summary": "Dynamic Frontend Engineer with expertise in React, TypeScript, and modern state architectures.",
        "tone": "Impactful",
        "key_strengths": ["React", "TypeScript", "UI Performance"],
        "variations": [
            "Frontend Engineer adept at delivering scalable responsive web applications.",
            "Specialist in React ecosystem delivering high-speed interfaces with clean architectures."
        ],
    }

    with patch(
        "app.services.gemini_service.gemini_service.improve_summary",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        payload = {
            "summary": "Junior developer with React experience.",
            "tone": "impactful",
        }
        response = client.post("/api/v1/resume/improve-summary", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["improved_summary"] == mock_result["improved_summary"]
        assert data["tone"] == "Impactful"
        assert len(data["variations"]) == 2
