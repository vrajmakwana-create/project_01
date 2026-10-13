from app.repository.base_repository import BaseRepository
from app.db.models.professional_summary_resume import ProfessionalSummaryResume
from sqlalchemy.orm import Session


class ProfessionalSummaryResumeRepository(BaseRepository[ProfessionalSummaryResume]):
    def __init__(self, db: Session):
        super().__init__(ProfessionalSummaryResume, db)
