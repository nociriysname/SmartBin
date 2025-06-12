from typing import Annotated, List, Optional

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from src.backend.core.database.async_engine import SessionDep
from src.backend.models.warehouses import Warehouse

__all__ = ("RepoWarehouse", "WarehouseRepoDep")


class RepoWarehouse:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        return await self.session.scalar(
            select(Warehouse).filter(Warehouse.warehouse_id == warehouse_id),
        )

    async def get_company_by_warehouse(
            self, warehouse_id: str,
    ) -> Mapped[str]:
        data = await self.get_by_id(warehouse_id)
        return data.company_id

    async def insert(self, warehouse: Warehouse) -> Warehouse:
        self.session.add(warehouse)
        await self.session.flush()
        await self.session.refresh(warehouse)
        return warehouse

    async def delete(self, warehouse_id: str) -> None:
        warehouse = await self.get_by_id(warehouse_id)
        await self.session.delete(warehouse)
        await self.session.flush()

    async def update(
        self,
        warehouse_id: str,
        location: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> Optional[Warehouse]:
        warehouse = await self.get_by_id(warehouse_id)

        update_data = {}

        if location is not None:
            update_data["location"] = location

        if latitude is not None:
            update_data["latitude"] = latitude

        if longitude is not None:
            update_data["longitude"] = longitude

        if update_data:
            await self.session.execute(
                update(Warehouse)
                .filter(Warehouse.warehouse_id == warehouse_id)
                .values(**update_data),
            )
            await self.session.flush()
            await self.session.refresh(warehouse)

        return warehouse

    async def get_all(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Warehouse], int]:
        query = (
            select(Warehouse)
            .filter(Warehouse.company_id == company_id)
            .limit(limit)
            .offset(offset)
        )
        users_result = await self.session.scalars(query)

        count_query = (
            select(func.count())
            .select_from(Warehouse)
            .filter(Warehouse.company_id == company_id)
        )
        total = await self.session.scalar(count_query)

        return list(users_result.all()), total


async def create_warehouse_repo(session: SessionDep) -> RepoWarehouse:
    return RepoWarehouse(session)


WarehouseRepoDep = Annotated[RepoWarehouse, Depends(create_warehouse_repo)]
