from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import current_user
from app.db.session import get_db
from app.schema.job_description import JobDescriptionAnalyzeRequest
from app.services.job_description_service import JobDescriptionService

router = APIRouter(prefix="/job-description", tags=["Job Description & Interview Prep"])


@router.post("/analyze")
async def analyze_job_description(
    request: Request,
    payload: JobDescriptionAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    service = JobDescriptionService(request, db)
    return await service.analyze_job_description(user["user_id"], payload)


@router.get("")
@router.get("/")
async def list_job_descriptions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    service = JobDescriptionService(request, db)
    return await service.list_analyses(user["user_id"])


@router.get("/{id}")
async def get_job_description(
    request: Request,
    id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    service = JobDescriptionService(request, db)
    return await service.get_analysis(user["user_id"], id)


@router.delete("/{id}")
async def delete_job_description(
    request: Request,
    id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    service = JobDescriptionService(request, db)
    return await service.delete_analysis(user["user_id"], id)
