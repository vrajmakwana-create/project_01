from fastapi import Depends
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logger import get_logger
from app.core.response import success_response, error_response
from app.core.exception_handler import setup_exception_handlers
from app.core.message import SuccessMessage
from app.core.limiter import limiter
from app.api.routes import app_router
from app.db import models
from app.core.dependecy import current_user

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} Started...")
    yield
    logger.info(f"{settings.APP_NAME} Shut Down...")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# Rate Limiter setup
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return error_response(
        status_code=429,
        msg="Rate limit exceeded: 5 attempts per minute. Please try again later.",
        data={"detail": str(exc.detail)},
    )


# Prometheus Instrumentation
Instrumentator().instrument(app).expose(app)

# Setup Exception Handlers (integrates fastapi-response-handler)
setup_exception_handlers(app)

# Register Router
app.include_router(app_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check():
    return success_response(msg=SuccessMessage.SERVER_HEALTHY)

@app.get("/server-test")
async def auth_server_check(
    user = Depends(current_user)
):
    return success_response(
        msg=SuccessMessage.AUTH_SERVER_HEALTHY
    )