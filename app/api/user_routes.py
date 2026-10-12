from app.core.dependecy import PermissionCheck
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependecy import RoleCheck, current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schema.user import UserLogin, UserOtpVerify, UserRegistration, UserChangePassword, UserRefreshToken
from app.services.user_service import UserService
from app.core.constants import Roles

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


@router.post("/change-password")
async def change_password(payload: UserChangePassword, request: Request, db: Session = Depends(get_db), user = Depends(current_user)):
    user_service = UserService(request, db)
    return await user_service.change_password(payload, user["user_id"])

@router.post("/refresh-token")
async def refresh_token(payload: UserRefreshToken, request:Request, db: Session = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.refresh_token(payload)

@router.get("/test-role")
async def test_role(user = Depends(current_user)):
    return success_response(
        status_code= 200,
        msg= "kdk"
    )