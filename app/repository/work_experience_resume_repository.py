from app.repository.base_repository import BaseRepository
from app.db.models.work_experience_resume import WorkExperienceResume
from sqlalchemy.ext.asyncio import AsyncSession


class WorkExperienceResumeRepository(BaseRepository[WorkExperienceResume]):
    def __init__(self, db: AsyncSession):
        super().__init__(WorkExperienceResume, db)
