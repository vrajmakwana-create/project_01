from app.repository.base_repository import BaseRepository
from app.db.models.projects_info_resume import ProjectInfoResume
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectInfoResumeRepository(BaseRepository[ProjectInfoResume]):
    def __init__(self, db: AsyncSession):
        super().__init__(ProjectInfoResume, db)
