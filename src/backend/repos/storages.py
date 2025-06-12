from typing import Annotated, List, Optional

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.enums import StopListReason
from src.backend.models.products import Products
from src.backend.models.shelves import Shelves
from src.backend.models.stoplist import StopList
from src.backend.models.storage import Storages

__all__ = ("RepoStorage", "StorageRepoDep")


class RepoStorage:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, storage_id: str) -> Optional[Storages]:
        return await self.session.scalar(
            select(Storages).filter(Storages.storage_id == storage_id),
        )

    async def get_all(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Storages], int]:
        query = (
            select(Storages)
            .filter(Storages.company_id == company_id)
            .limit(limit)
            .offset(offset)
        )
        users_result = await self.session.scalars(query)

        count_query = (
            select(func.count())
            .select_from(Storages)
            .filter(Storages.company_id == company_id)
        )
        total = await self.session.scalar(count_query)

        return list(users_result.all()), total

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

    async def get_shelves_by_company(self, company_id: str) -> List[Shelves]:
        query = (
            select(Shelves)
            .join(Storages, Storages.storage_id == Shelves.storage_id)
            .where(Storages.company_id == company_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def insert_storage(self, storage: Storages) -> Storages:
        self.session.add(storage)
        await self.session.flush()
        await self.session.refresh(storage)
        return storage

    async def delete_storage(self, storage_id: str) -> None:
        storage = await self.get_by_id(storage_id)
        await self.session.delete(storage)
        await self.session.flush()

    async def insert_shelf(self, shelf: Shelves) -> Shelves:
        self.session.add(shelf)
        await self.session.flush()
        await self.session.refresh(shelf)
        return shelf

    async def delete_shelf(self, shelf_id: str) -> None:
        shelf = self.get_shelf_by_id(shelf_id)
        await self.session.delete(shelf)
        await self.session.flush()

    async def get_shelves_by_storage(
        self,
        storage_id: str,
    ) -> list[Shelves]:
        return list(
            await self.session.scalars(
                select(Shelves).filter(Shelves.storage_id == storage_id),
            ),
        )

    async def get_shelf_by_id(self, shelf_id: str) -> Optional[Shelves]:
        return await self.session.scalar(
            select(Shelves).filter(Shelves.shelf_id == shelf_id),
        )

    async def get_product_by_barcode(self, barcode: str) -> Optional[Products]:
        return await self.session.scalar(
            select(Products).filter(Products.barcode == barcode),
        )

    async def get_product_by_article(self, article: str) -> Optional[Products]:
        return await self.session.scalar(
            select(Products).filter(Products.article == article),
        )

    async def get_product_by_id(self, product_id: str) -> Optional[Products]:
        return await self.session.scalar(
            select(Products).filter(Products.item_id == product_id),
        )

    async def insert_stoplist_entry(
        self,
        product_id: str,
        reason: StopListReason,
    ) -> StopList:
        stoplist_entry = StopList(product_id=product_id, reason=reason)
        self.session.add(stoplist_entry)
        await self.session.flush()
        await self.session.refresh(stoplist_entry)
        return stoplist_entry

    async def delete_stoplist_entry(
        self,
        product_id: str,
    ) -> None:
        stoplist_entry = await self.get_stoplist_entry_by_id(product_id)
        await self.session.delete(stoplist_entry)
        await self.session.flush()

    async def get_stoplist_entry_by_id(
        self,
        warehouse_id: str,
    ) -> Optional[StopList]:
        return await self.session.scalar(
            select(StopList).filter(StopList.warehouse_id == warehouse_id),
        )


async def create_storage_repo(session: SessionDep) -> RepoStorage:
    return RepoStorage(session)


StorageRepoDep = Annotated[RepoStorage, Depends(create_storage_repo)]
