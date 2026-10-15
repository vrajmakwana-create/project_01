"""
Base repository class with asynchronous CRUD operations using SQLAlchemy 2.0 select.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.common.utils import get_unix_time

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository providing asynchronous CRUD operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(
        self, id: str, active_only: bool = True, include_deleted: bool = False
    ) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        if active_only and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_field(
        self, field_name: str, value: Any, active_only: bool = True, include_deleted: bool = False
    ) -> Optional[ModelType]:
        if not hasattr(self.model, field_name):
            raise ValueError(f"Invalid model field: {field_name}")

        stmt = select(self.model).where(getattr(self.model, field_name) == value)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        if active_only and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        active_only: bool = True,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)
        if active_only and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active == True)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: Union[Dict[str, Any], BaseModel]) -> ModelType:
        if isinstance(obj_in, BaseModel):
            data = obj_in.model_dump()
        else:
            data = obj_in

        db_obj = self.model(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: str) -> bool:
        obj = await self.get(id, active_only=False, include_deleted=False)
        if not obj:
            return False
        if hasattr(obj, "is_deleted"):
            obj.is_deleted = True
            if hasattr(obj, "is_active"):
                obj.is_active = False
            if hasattr(obj, "deleted_at"):
                obj.deleted_at = get_unix_time()
            await self.db.flush()
        else:
            await self.db.delete(obj)
            await self.db.flush()
        await self.db.commit()
        return True
