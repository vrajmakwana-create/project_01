import secrets
from typing import Optional, Tuple
from datetime import datetime, timezone
from pydantic import EmailStr
from app.services.email_service import email_service


def get_unix_time() -> int:
    """Return UNIX TIME in milliseconds."""
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def generate_otp() -> int:
    """Return cryptographically secure 6-digit random number (100000 to 999999)."""
    return 100000 + secrets.randbelow(900000)


async def send_email_verification_email(
    email: EmailStr,
    full_name: str,
    otp: Optional[int] = None,
    otp_expiry: Optional[int] = None,
) -> Tuple[int, int]:
    """Sends OTP verification email and returns (otp, otp_expiry)."""
    if otp is None or otp_expiry is None:
        otp_expiry = get_unix_time() + (5 * 60 * 1000)  # 5 minutes in ms
        otp = generate_otp()

    await email_service.send_otp_email(
        to_email=email,
        otp=otp,
        name=full_name,
    )
    return otp, otp_expiry
