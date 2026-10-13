from app.repository.base_repository import BaseRepository
from app.db.models.educational_info_resume import EducationalInfoResume
from sqlalchemy.ext.asyncio import AsyncSession


class EducationalInfoResumeRepository(BaseRepository[EducationalInfoResume]):
    def __init__(self, db: AsyncSession):
        super().__init__(EducationalInfoResume, db)
