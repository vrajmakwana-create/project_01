from app.repository.base_repository import BaseRepository
from app.db.models.skill_resume import SkillResume
from sqlalchemy.ext.asyncio import AsyncSession


class SkillResumeRepository(BaseRepository[SkillResume]):
    def __init__(self, db: AsyncSession):
        super().__init__(SkillResume, db)
