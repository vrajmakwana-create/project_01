from typing import Optional
from fastapi import BackgroundTasks, HTTPException, Request, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils import generate_otp, get_unix_time, send_email_verification_email
from app.core.constants import (
    Roles,
    JWT_ACCESS_TOKEN_EXPIRY_TIME,
    JWT_REFRESH_TOKEN_EXPIRY_TIME,
)
from app.core.enums import LoginType
from app.core.exception import ServerException
from app.core.logger import get_logger
from app.core.message import ErrorMessage, SuccessMessage
from app.core.response import success_response
from app.db.models.user import User
from app.repository.role_repository import RoleRepository
from app.repository.user_repository import UserRepository
from app.repository.user_session_repository import UserSessionRepository
from app.schema.user import (
    UserDetail,
    UserLogin,
    UserLoginResponse,
    UserOtpVerify,
    UserOTPVerifyResponse,
    UserRegistration,
    UserRegistrationResponse,
    UserChangePassword, 
    UserRefreshToken,
    UserRefreshTokenResponse
)
from app.core.hash import verify_password
from app.core.jwt import generate_token, verify_token

logger = get_logger(__name__)


class UserService:
    def __init__(
        self,
        request: Request,
        db: AsyncSession,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        self.request = request
        self.db = db
        self.background_tasks = background_tasks
        self.user_repo = UserRepository(self.db)
        self.role_repo = RoleRepository(self.db)
        self.user_session_repo = UserSessionRepository(self.db)

    def _dispatch_background_task(self, func, *args, **kwargs):
        """Dispatches a heavy task in the background using FastAPI BackgroundTasks or asyncio loop."""
        if self.background_tasks:
            self.background_tasks.add_task(func, *args, **kwargs)
        else:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(func(*args, **kwargs))
            except RuntimeError:
                logger.warning("No running event loop available to dispatch background task.")
    
    async def get_user(self, user_id: str):
        try:
            user = await self.user_repo.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.USER_NOT_FOUND,
                )
            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.USER_FETCHED_SUCCESSFULLY,
                data=UserDetail.model_validate(user).model_dump(),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def register_user(self, payload: UserRegistration):
        try:
            email = payload.email
            first_name = payload.first_name
            last_name = payload.last_name
            full_name = f"{first_name} {last_name}"

            user_detail = await self.user_repo.get_by_field("email", email, active_only=False)

            if user_detail and user_detail.is_verified:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.USER_ALREADY_EXIST,
                )
            elif user_detail and not user_detail.is_verified:
                # new_otp = generate_otp()
                new_otp = 111111
                new_expiry = get_unix_time() + (5 * 60 * 1000)
                user_detail.otp = new_otp
                user_detail.otp_expiry = new_expiry
                await self.db.commit()
                await self.db.refresh(user_detail)

                # Dispatch heavy email task to background
                self._dispatch_background_task(
                    send_email_verification_email,
                    email=email,
                    full_name=full_name,
                    otp=new_otp,
                    otp_expiry=new_expiry,
                )

                return success_response(
                    status_code=http_status.HTTP_200_OK,
                    msg=SuccessMessage.USER_VERIFICATION_EMAIL_SEND,
                    data=UserRegistrationResponse.model_validate(user_detail).model_dump(),
                )

            # otp = generate_otp()
            otp = 111111
            otp_expiry = get_unix_time() + (5 * 60 * 1000)
            user_data = payload.model_dump()
            user_data.update(
                {
                    "otp_expiry": otp_expiry,
                    "otp": otp,
                }
            )

            role_detail = await self.role_repo.get_by_field("role_name", Roles.EMPLOYEE)
            if not role_detail:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.ROLE_NOT_FOUND,
                )

            user_data.update(
                {
                    "role_id": role_detail.id,
                    "is_active": False,
                    "login_type": LoginType.EMAIL,
                }
            )

            new_user = User(**user_data)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)

            # Dispatch heavy email task to background
            self._dispatch_background_task(
                send_email_verification_email,
                email=email,
                full_name=full_name,
                otp=otp,
                otp_expiry=otp_expiry,
            )

            response_data = UserRegistrationResponse.model_validate(new_user).model_dump()

            return success_response(
                status_code=http_status.HTTP_201_CREATED,
                msg=SuccessMessage.USER_REGISTERED_SUCCESSFULLY,
                data=response_data,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(str(e))

    async def verify_otp(self, payload: UserOtpVerify):
        try:
            user_id = payload.user_id
            otp = payload.otp

            user = await self.user_repo.get(user_id, active_only=False)
            if not user:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if user.is_verified and not user.is_deleted:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.USER_ALREADY_VERIFIED,
                )

            current_time = get_unix_time()
            if user.otp_expiry and user.otp_expiry < current_time:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.OTP_EXPIRED,
                )

            if user.otp != otp:
                raise HTTPException(
                    status_code=http_status.HTTP_401_UNAUTHORIZED,
                    detail=ErrorMessage.OTP_INVALID,
                )

            user.is_verified = True
            user.is_active = True

            await self.db.commit()
            await self.db.refresh(user)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.USER_OTP_VERIFIED_SUCCESSFULLY,
                data=UserOTPVerifyResponse.model_validate(user).model_dump(),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def login_user(self, payload: UserLogin):
        try:
            email = payload.email
            password = payload.password
            device_id = payload.device_id

            user = await self.user_repo.get_by_field("email", email, active_only=False)
            if not user:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessage.USER_INACTIVE,
                )

            if not verify_password(password, user.password):
                raise HTTPException(
                    status_code=http_status.HTTP_401_UNAUTHORIZED,
                    detail=ErrorMessage.INVALID_CREDENTIALS,
                )
            
            token_payload = {
                "user_id": str(user.id),
                "role_id": str(user.role_id),
            }

            access_token = generate_token(
                token_payload, expiry_time_in_min=JWT_ACCESS_TOKEN_EXPIRY_TIME
            )
            refresh_token = generate_token(
                token_payload, expiry_time_in_min=JWT_REFRESH_TOKEN_EXPIRY_TIME
            )

            # Store / Update Active User Session asynchronously
            user_session_data = {
                "user_id": user.id,
                "session": access_token,
                "refresh_token": refresh_token
            }
            await self.user_session_repo.add_user_session(user_session_data)

            response_data = UserLoginResponse(
                user=UserDetail.model_validate(user),
                access_token=access_token,
                refresh_token=refresh_token,
            ).model_dump()

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.USER_LOGIN_SUCCESSFULLY,
                data=response_data,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def change_password(self, payload: UserChangePassword, user_id: str):
        try:
            user = await self.user_repo.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.USER_NOT_FOUND,
                )

            if not verify_password(payload.old_password, user.password):
                raise HTTPException(
                    status_code=http_status.HTTP_401_UNAUTHORIZED,
                    detail=ErrorMessage.WRONG_OLD_PASSWORD,
                )

            user.password = payload.new_password

            # Invalidate all user sessions upon password change for security
            user_sessions = await self.user_session_repo.get_all(filters={"user_id": user_id}, active_only=False)
            for session_item in user_sessions:
                await self.db.delete(session_item)

            await self.db.commit()
            await self.db.refresh(user)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.USER_CHANGE_PASSWORD_SUCCESSFULLY,
                data=None,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))

    async def refresh_token(self, payload: UserRefreshToken):
        try:
            refresh_token = payload.refresh_token
            user_session = await self.user_session_repo.get_by_field("refresh_token", refresh_token)

            if not user_session:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=ErrorMessage.USER_SESSION_NOT_FOUND,
                )
            
            # Check Expiry of Refresh Token
            payload_data = verify_token(refresh_token)
            
            token_payload = {
                "user_id": str(payload_data["user_id"]),
                "role_id": str(payload_data["role_id"]),
            }

            access_token = generate_token(
                token_payload, expiry_time_in_min=JWT_ACCESS_TOKEN_EXPIRY_TIME
            )
            refresh_token_new = generate_token(
                token_payload, expiry_time_in_min=JWT_REFRESH_TOKEN_EXPIRY_TIME
            )

            user_session.session = access_token
            user_session.refresh_token = refresh_token_new
            await self.db.commit()
            await self.db.refresh(user_session)

            return success_response(
                status_code=http_status.HTTP_200_OK,
                msg=SuccessMessage.USER_SESSION_REFRESHED_SUCCESSFULLY,
                data=UserRefreshTokenResponse.model_validate({
                    "access_token": access_token,
                    "refresh_token": refresh_token_new
                })
            )
        except HTTPException:
            raise
        except Exception as e:
            raise ServerException(message=str(e))