from typing import Annotated, Optional, TypeVar

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.backend.core.database.async_engine import SessionDep
from src.backend.models.storage import Storages

__all__ = ("RepoStorage", "StorageRepoDep")

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class RepoStorage:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_storage_id(self, storage_id: str) -> Optional[Storages]:
        return await self.session.scalar(
            select(Storages).filter(Storages.storage_id == storage_id),
        )

    async def get_storage_by_warehouse(
        self,
        warehouse_id: str,
        company_id: str,
    ) -> Optional[Storages]:
        return await self.session.scalar(
            select(Storages).filter(
                Storages.warehouse_id == warehouse_id,
                Storages.company_id == company_id,
            ),
        )

    async def create_storage(self, storage: Storages) -> Storages:
        self.session.add(storage)
        await self.session.commit()
        await self.session.refresh(storage)
        return storage


async def create_storage_repo(session: SessionDep) -> RepoStorage:
    return RepoStorage(session)


StorageRepoDep = Annotated[RepoStorage, Depends(create_storage_repo)]
