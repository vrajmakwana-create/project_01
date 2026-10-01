from fastapi import Request, HTTPException
from app.core.exception import ServerException
from app.core.response import error_response
from app.core.logger import get_logger

try:
    from fastapi_response_handler import register_exception_handlers
    HAS_RESPONSE_HANDLER = True
except ImportError:
    HAS_RESPONSE_HANDLER = False

logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(status_code=exc.status_code, msg=exc.detail)


async def server_exception_handler(request: Request, exc: ServerException):
    logger.error(exc.message, exc_info=True)
    return error_response(
        status_code=exc.status_code,
        msg=exc.message
    )


def setup_exception_handlers(app):
    """Registers exception handlers on the FastAPI application."""
    if HAS_RESPONSE_HANDLER:
        register_exception_handlers(app)
    else:
        app.add_exception_handler(HTTPException, http_exception_handler)
        app.add_exception_handler(ServerException, server_exception_handler)
