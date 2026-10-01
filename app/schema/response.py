from pydantic import BaseModel
from typing import Any, Optional
from fastapi import status as http_status
from app.core.message import ErrorMessage, SuccessMessage


class ErrorMessageResponse(BaseModel):
    status: Optional[int] = http_status.HTTP_500_INTERNAL_SERVER_ERROR
    msg: Optional[str] = ErrorMessage.INTERNAL_SERVER_ERROR
    data: Optional[Any] = None


class SuccessMessageResponse(BaseModel):
    status: Optional[int] = http_status.HTTP_200_OK
    msg: Optional[str] = SuccessMessage.RESPONSE_FETCHED_SUCCESSFULLY
    data: Optional[Any] = {}
