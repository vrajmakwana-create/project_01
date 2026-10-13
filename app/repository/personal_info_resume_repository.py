from app.repository.base_repository import BaseRepository
from app.db.models.personal_info_resume import PersonalInfoResume
from sqlalchemy.orm import Session


class PersonalInfoResumeRepository(BaseRepository[PersonalInfoResume]):
    def __init__(self, db: Session):
        super().__init__(PersonalInfoResume, db)
