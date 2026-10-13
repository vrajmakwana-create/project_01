from app.repository.base_repository import BaseRepository
from app.db.models.skill_resume import SkillResume
from sqlalchemy.orm import Session


class SkillResumeRepository(BaseRepository[SkillResume]):
    def __init__(self, db: Session):
        super().__init__(SkillResume, db)
