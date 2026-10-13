from app.repository.base_repository import BaseRepository
from app.db.models.projects_info_resume import ProjectInfoResume
from sqlalchemy.orm import Session


class ProjectInfoResumeRepository(BaseRepository[ProjectInfoResume]):
    def __init__(self, db: Session):
        super().__init__(ProjectInfoResume, db)
