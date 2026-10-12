from fastapi import APIRouter
from app.api.user_routes import router as user_router
from app.api.resume_routes import router as resume_router

app_router = APIRouter()

app_router.include_router(user_router)
app_router.include_router(resume_router)
