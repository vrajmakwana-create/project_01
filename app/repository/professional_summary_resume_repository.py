from app.repository.base_repository import BaseRepository
from app.db.models.professional_summary_resume import ProfessionalSummaryResume
from sqlalchemy.ext.asyncio import AsyncSession


class ProfessionalSummaryResumeRepository(BaseRepository[ProfessionalSummaryResume]):
    def __init__(self, db: AsyncSession):
        super().__init__(ProfessionalSummaryResume, db)
