from typing import Optional
from datetime import datetime, timezone
from random import randint
from pydantic import EmailStr
from app.services.email_service import email_service


def get_unix_time() -> int:
    """Return UNIX TIME in milliseconds."""
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def generate_otp() -> int:
    """Return 4 digit random number."""
    return int("".join([str(randint(a=1, b=9)) for _ in range(4)]))


async def send_email_verification_email(
    email: EmailStr,
    full_name: str,
    otp: Optional[int] = None,
    otp_expiry: Optional[int] = None,
) -> None:
    if otp is None or otp_expiry is None:
        otp_expiry = get_unix_time() + (5 * 60 * 1000)  # 5 minutes
        otp = generate_otp()

    await email_service.send_otp_email(
        to_email=email,
        otp=otp,
        name=full_name,
    )
