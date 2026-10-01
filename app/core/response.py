from typing import Optional, Any
from fastapi import status as http_status
from fastapi.responses import JSONResponse

try:
    from fastapi_response_handler import success_response as rh_success, error_response as rh_error
    HAS_RESPONSE_HANDLER = True
except ImportError:
    HAS_RESPONSE_HANDLER = False

from app.schema.response import ErrorMessageResponse, SuccessMessageResponse
from app.core.message import ErrorMessage


def success_response(
    status_code: int = http_status.HTTP_200_OK,
    msg: Optional[str] = None,
    data: Optional[Any] = None,
):
    """Standard success response helper, integrated with fastapi-response-handler."""
    if HAS_RESPONSE_HANDLER:
        return rh_success(status_code=status_code, msg=msg, data=data)

    message = SuccessMessageResponse(status=status_code, msg=msg, data=data)
    return JSONResponse(status_code=status_code, content=message.model_dump())


def error_response(
    status_code: int = http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    msg: Optional[str] = ErrorMessage.INTERNAL_SERVER_ERROR,
    data: Optional[Any] = None,
):
    """Standard error response helper, integrated with fastapi-response-handler."""
    if HAS_RESPONSE_HANDLER:
        return rh_error(status_code=status_code, msg=msg, data=data)

    message = ErrorMessageResponse(status=status_code, msg=msg, data=data)
    return JSONResponse(status_code=status_code, content=message.model_dump())
