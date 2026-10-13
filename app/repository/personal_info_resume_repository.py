from app.repository.base_repository import BaseRepository
from app.db.models.personal_info_resume import PersonalInfoResume
from sqlalchemy.ext.asyncio import AsyncSession


class PersonalInfoResumeRepository(BaseRepository[PersonalInfoResume]):
    def __init__(self, db: AsyncSession):
        super().__init__(PersonalInfoResume, db)
