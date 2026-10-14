import uuid
from app.db.models.user import User


def test_user_signup_and_verify_flow(client, db_session, mock_email_service):
    unique_email = f"signup_{uuid.uuid4().hex[:8]}@example.com"
    signup_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": unique_email,
        "password": "SecurePassword123!",
    }

    # 1. Signup
    signup_resp = client.post("/api/v1/users/email-signup", json=signup_payload)
    assert signup_resp.status_code == 201
    user_data = signup_resp.json()["data"]
    user_id = user_data["id"]
    assert user_data["is_verified"] is False

    # Verify background email verification was executed
    assert mock_email_service.called
    call_kwargs = mock_email_service.call_args.kwargs
    assert call_kwargs["to_email"] == unique_email

    # 2. Retrieve OTP from DB (as email is mocked/dev)
    user_in_db = db_session.query(User).filter(User.id == user_id).first()
    assert user_in_db is not None
    assert user_in_db.is_active is False
    otp = user_in_db.otp

    # 3. Verify OTP
    verify_resp = client.post("/api/v1/users/verify-otp", json={"user_id": user_id, "otp": otp})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["data"]["is_verified"] is True

    # Check DB state
    db_session.refresh(user_in_db)
    assert user_in_db.is_active is True
    assert user_in_db.is_verified is True

    # 4. Login
    login_resp = client.post("/api/v1/users/login", json={
        "email": unique_email,
        "password": "SecurePassword123!",
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()["data"]
    assert "access_token" in login_data
    assert "refresh_token" in login_data


def test_unverified_user_resend_verification_email(client, db_session, mock_email_service):
    unique_email = f"resend_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": unique_email,
        "password": "SecurePassword123!",
    }

    # Initial registration (unverified)
    resp1 = client.post("/api/v1/users/email-signup", json=payload)
    assert resp1.status_code == 201
    mock_email_service.reset_mock()

    # Re-registration before verification triggers resending verification email in background
    resp2 = client.post("/api/v1/users/email-signup", json=payload)
    assert resp2.status_code == 200

    # Ensure background email dispatch was invoked
    assert mock_email_service.called
    call_kwargs = mock_email_service.call_args.kwargs
    assert call_kwargs["to_email"] == unique_email


def test_login_invalid_credentials(client):
    response = client.post("/api/v1/users/login", json={
        "email": "nonexistent_email_12345@example.com",
        "password": "WrongPassword",
    })
    # Could be 404 (user not found) or 429 if limit is reached
    assert response.status_code in (404, 429)


def test_unauthorized_access(client):
    response = client.get("/api/v1/users/test-role")
    assert response.status_code == 401


def test_rate_limiting_shield(client):
    """Ensure sending more than 5 attempts within a minute triggers HTTP 429 Too Many Requests."""
    responses = []
    for i in range(7):
        resp = client.post("/api/v1/users/verify-otp", json={
            "user_id": f"fake_id_{i}",
            "otp": 123456,
        })
        responses.append(resp.status_code)

    assert 429 in responses
