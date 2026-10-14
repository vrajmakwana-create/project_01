from pathlib import Path
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
from app.db.models.user_information import UserInformation
from app.db.models.personal_info_resume import PersonalInfoResume
from app.db.models.professional_summary_resume import ProfessionalSummaryResume
from app.db.models.skill_resume import SkillResume
from app.db.models.educational_info_resume import EducationalInfoResume
from app.db.models.work_experience_resume import WorkExperienceResume
from app.db.models.projects_info_resume import ProjectInfoResume
from app.core.hash import password_hash
from app.core.constants import Roles


def delete_user_and_related_data(db_session, user_id: str):
    """Deletes a user and all their related resume and session records across all tables."""
    try:
        user_id_str = str(user_id)
        db_session.query(PersonalInfoResume).filter(PersonalInfoResume.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(ProfessionalSummaryResume).filter(ProfessionalSummaryResume.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(SkillResume).filter(SkillResume.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(EducationalInfoResume).filter(EducationalInfoResume.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(WorkExperienceResume).filter(WorkExperienceResume.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(ProjectInfoResume).filter(ProjectInfoResume.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(UserInformation).filter(UserInformation.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(UserSession).filter(UserSession.user_id == user_id_str).delete(synchronize_session=False)
        db_session.query(User).filter(User.id == user_id_str).delete(synchronize_session=False)
        db_session.commit()
    except Exception:
        db_session.rollback()


def cleanup_test_files():
    """Removes any temporary resume files generated during tests."""
    upload_dir = Path("uploads/resumes")
    if upload_dir.exists():
        for f in upload_dir.glob("*.pdf"):
            try:
                f.unlink()
            except Exception:
                pass


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


@pytest.fixture(autouse=True, scope="function")
def auto_cleanup_db():
    """Runs after every single test function to ensure absolutely no test data remains in DB."""
    yield
    db = SessionLocal()
    try:
        # Delete any test users created by auth tests or other helpers
        test_users = db.query(User).filter(
            (User.email.like("test_%@example.com")) |
            (User.email.like("signup_%@example.com")) |
            (User.email.like("resend_%@example.com")) |
            (User.email.like("%@example.com"))
        ).all()
        for u in test_users:
            delete_user_and_related_data(db, str(u.id))
    except Exception:
        db.rollback()
    finally:
        db.close()
    
    cleanup_test_files()


@pytest.fixture(autouse=True, scope="session")
def auto_cleanup_session():
    """Wipes test data before and after the entire pytest session."""
    def _wipe():
        db = SessionLocal()
        try:
            test_users = db.query(User).filter(
                (User.email.like("test_%@example.com")) |
                (User.email.like("signup_%@example.com")) |
                (User.email.like("resend_%@example.com")) |
                (User.email.like("%@example.com"))
            ).all()
            for u in test_users:
                delete_user_and_related_data(db, str(u.id))
        except Exception:
            db.rollback()
        finally:
            db.close()
        cleanup_test_files()

    _wipe()
    yield
    _wipe()


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

    # Teardown
    delete_user_and_related_data(db_session, str(user.id))
