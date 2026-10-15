from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RoleCheck, PermissionCheck, current_user
from app.core.response import success_response
from app.core.limiter import limiter
from app.db.session import get_db
from app.schema.user import (
    UserLogin,
    UserOtpVerify,
    UserRegistration,
    UserChangePassword,
    UserRefreshToken,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_user(request: Request, db: AsyncSession = Depends(get_db), user = Depends(current_user)):
    user_service = UserService(request, db)
    return await user_service.get_user(user.get("user_id"))

@router.post("/email-signup")
async def email_signup(
    payload: UserRegistration,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(request, db, background_tasks=background_tasks)
    return await user_service.register_user(payload)


@router.post("/verify-otp")
@limiter.limit("5/minute")
async def verify_otp(payload: UserOtpVerify, request: Request, db: AsyncSession = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.verify_otp(payload)


@router.post("/login")
@limiter.limit("100/minute")
async def email_login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.login_user(payload)


@router.post("/change-password")
async def change_password(
    payload: UserChangePassword,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    user_service = UserService(request, db)
    return await user_service.change_password(payload, user["user_id"])


@router.post("/refresh-token")
async def refresh_token(payload: UserRefreshToken, request: Request, db: AsyncSession = Depends(get_db)):
    user_service = UserService(request, db)
    return await user_service.refresh_token(payload)


# TODO: Forgot Password
@router.post("/forgot-password")
async def forgot_password(payload: UserRefreshToken, request: Request, db: AsyncSession = Depends(get_db)):
    pass


# TODO: Reset Password
@router.post("/reset-password")
async def reset_password(payload: UserRefreshToken, request: Request, db: AsyncSession = Depends(get_db)):
    pass


@router.get("/test-role")
async def test_role(user=Depends(current_user)):
    return success_response(
        status_code=200,
        msg="Done",
    )