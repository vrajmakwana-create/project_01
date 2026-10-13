from app.repository.base_repository import BaseRepository
from app.db.models.work_experience_resume import WorkExperienceResume
from sqlalchemy.orm import Session


class WorkExperienceResumeRepository(BaseRepository[WorkExperienceResume]):
    def __init__(self, db: Session):
        super().__init__(WorkExperienceResume, db)
