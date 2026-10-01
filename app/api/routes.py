from fastapi import APIRouter
from app.api.user_routes import router as user_router

app_router = APIRouter()

app_router.include_router(user_router)
