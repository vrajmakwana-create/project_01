from app.core.dependecy import PermissionCheck
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependecy import RoleCheck, current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schema.user import UserLogin, UserOtpVerify, UserRegistration
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/email-signup")
async def email_signup(payload: UserRegistration, request: Request, db: Session = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.register_user(payload)


@router.post("/verify-otp")
async def verify_otp(payload: UserOtpVerify, request: Request, db: Session = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.verify_otp(payload)


@router.post("/login")
async def email_login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.login_user(payload)


@router.get("/test-role")
async def test_role_check(payload: dict = Depends(PermissionCheck(permissions=["delete"]))):
    return success_response(
        msg="RoleCheck dependency is working successfully!",
        data={"user_payload": payload},
    )
