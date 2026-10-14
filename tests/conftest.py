from unittest.mock import AsyncMock, patch
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.core.jwt import generate_token
from app.db.models.user import User
from app.db.models.role import Role
from app.db.models.user_session import UserSession
from app.core.hash import password_hash
from app.core.constants import Roles


@pytest.fixture(autouse=True)
def mock_email_service():
    """Mocks email_service.send_otp_email to isolate tests from real network calls."""
    with patch("app.services.email_service.email_service.send_otp_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        yield mock_send


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Creates a temporary verified test user with active session."""
    # Ensure employee role exists
    role = db_session.query(Role).filter(Role.role_name == Roles.EMPLOYEE).first()
    if not role:
        role = Role(id=str(uuid.uuid4()), role_name=Roles.EMPLOYEE, is_active=True, is_deleted=False)
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)

    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=str(uuid.uuid4()),
        first_name="Test",
        last_name="User",
        email=unique_email,
        password=password_hash("Password@123"),
        is_verified=True,
        is_active=True,
        is_deleted=False,
        role_id=role.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generate token
    token_payload = {"user_id": str(user.id), "role_id": str(user.role_id)}
    token = generate_token(token_payload)

    # Add user session
    session_obj = UserSession(
        id=str(uuid.uuid4()),
        user_id=str(user.id),
        session=token,
        refresh_token=token,
        is_active=True,
        is_deleted=False,
    )
    db_session.add(session_obj)
    db_session.commit()

    yield {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

    # Cleanup
    try:
        db_session.query(UserSession).filter(UserSession.user_id == str(user.id)).delete()
        db_session.query(User).filter(User.id == str(user.id)).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()
