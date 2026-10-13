from app.repository.base_repository import BaseRepository
from app.db.models.educational_info_resume import EducationalInfoResume
from sqlalchemy.orm import Session


class EducationalInfoResumeRepository(BaseRepository[EducationalInfoResume]):
    def __init__(self, db: Session):
        super().__init__(EducationalInfoResume, db)
