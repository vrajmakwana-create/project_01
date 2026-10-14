from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.base_repository import BaseRepository
from app.db.models.job_description import JobDescription


class JobDescriptionRepository(BaseRepository[JobDescription]):
    def __init__(self, db: AsyncSession):
        super().__init__(JobDescription, db)
