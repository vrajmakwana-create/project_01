from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import get_logger
from app.core.response import success_response
from app.core.exception_handler import setup_exception_handlers
from app.core.message import SuccessMessage
from app.api.routes import app_router
from app.db import models

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

# Setup Exception Handlers (integrates fastapi-response-handler)
setup_exception_handlers(app)

# Register Router
app.include_router(app_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check():
    return success_response(msg=SuccessMessage.SERVER_HEALTHY)
