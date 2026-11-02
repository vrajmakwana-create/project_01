from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import current_user
from app.db.session import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("", summary="Get Dashboard Analytics")
@router.get("/", summary="Get Dashboard Analytics")
async def get_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_user),
):
    service = DashboardService(request, db)
    return await service.get_dashboard_analytics(user["user_id"])

