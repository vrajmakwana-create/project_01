from datetime import datetime, timezone, timedelta
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from fastapi import HTTPException, status as http_status
from app.core.config import settings
from app.core.message import ErrorMessage, LoggerMessage
from app.core.constants import JWT_ACCESS_TOKEN_EXPIRY_TIME
from app.core.logger import get_logger

logger = get_logger(__name__)

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM


def generate_token(
    payload: dict, expiry_time_in_min: int = JWT_ACCESS_TOKEN_EXPIRY_TIME
) -> str:
    payload_copy = payload.copy()
    payload_copy.update(
        {
            "exp": int(
                (
                    datetime.now(tz=timezone.utc)
                    + timedelta(minutes=expiry_time_in_min)
                ).timestamp()
            )
        }
    )
    return jwt.encode(payload_copy, key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    user_id = None
    try:
        payload = jwt.decode(token=token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id", "Unknown")
        return payload
    except ExpiredSignatureError as e:
        logger.error(
            LoggerMessage.ExpiredSignatureError_Logtext.format(user_id=user_id, e=e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.TOKEN_EXPIRE,
        )
    except JWTError as e:
        logger.error(
            LoggerMessage.ExpiredSignatureError_Logtext.format(user_id=user_id, e=e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.INVALID_TOKEN,
        )
