from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.hash import password_hash


class UserRegistration(BaseModel):
    first_name: str = Field(..., description="First name of the User")
    last_name: str = Field(..., description="Last name of the User")
    email: EmailStr = Field(..., description="Email of user")
    password: str = Field(..., description="Password of user account")

    @field_validator("password", mode="after")
    def hash_password(cls, v: str) -> str:
        return password_hash(v)


class UserOtpVerify(BaseModel):
    user_id: str
    otp: int


class UserRegistrationResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    is_verified: bool
    role_id: str

    model_config = ConfigDict(from_attributes=True)


class UserOTPVerifyResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


# Login User Schema
class UserLogin(BaseModel):
    email: str
    password: str
    device_id: Optional[str] = None


class UserDetail(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    is_verified: bool
    role_id: str

    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserDetail