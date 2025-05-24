from typing import Annotated, Any, List, Optional, Type, TypeVar

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.models.access_level import UserAccess
from src.backend.models.users import Users
from src.backend.models.warehouses import Warehouse

__all__ = ("RepoWarehouse", "WarehouseRepoDep")

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class RepoWarehouse:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    async def _get_company_id_filter(
        stmt: Any,
        company_id: str,
        model: Type[ModelType],
    ) -> Any:
        return stmt.filter(model.company_id == company_id)

    async def get_all_warehouses(
        self,
        company_id: str,
        size: int = 50,
        page: int = 0,
        location: Optional[str] = None,
    ) -> tuple[List[Warehouse], int]:
        stmt = select(Warehouse).order_by(Warehouse.created_at.desk())
        stmt = await self._get_company_id_filter(stmt, company_id, Warehouse)
        if location:
            stmt = stmt.filter(Warehouse.location == location)

        return await self._get_paginated_list(stmt, size, page)

    async def create_new_warehouse(
        self,
        company_id: str,
        warehouse: Warehouse,
        location: str,
        coordinates: list[float],
    ) -> Warehouse:
        warehouse.company_id = company_id
        warehouse.location = location
        warehouse.longitude, warehouse.latitude = coordinates
        self.session.add(warehouse)
        await self.session.commit()
        await self.session.refresh(warehouse)
        return warehouse

    async def delete_warehouse(
        self,
        company_id: str,
        warehouse_id: str,
    ) -> None:
        warehouse = self.get_by_id(warehouse_id, company_id)

        if not warehouse:
            raise NotFoundError("Warehouse not found")

        await self.session.delete(warehouse)
        await self.session.commit()

    async def update_warehouse_info(
        self,
        company_id: str,
        warehouse_id: str,
        location: Optional[str] = None,
        coordinates: Optional[list[float]] = None,
    ) -> Warehouse:
        warehouse = await self.get_by_id(company_id, warehouse_id)
        if location:
            warehouse.location = location

        if coordinates:
            warehouse.longitude, warehouse.latitude = coordinates

        if not warehouse:
            raise NotFoundError(message="Warehouse not found")

        await self.session.commit()
        await self.session.refresh(warehouse)
        return warehouse

    async def get_warehouse_userroles(
        self,
        warehouse_id: str,
        company_id: str,
    ) -> List[Users]:
        warehouse = await self.get_by_id(warehouse_id, company_id)
        if not warehouse:
            raise NotFoundError("Warehouse not found")

        stmt = await self._get_company_id_filter(
            select(Users)
            .join(UserAccess)
            .filter(UserAccess.warehouse_id == warehouse_id),
            company_id,
            Users,
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_id(self, warehouse_id: str, company_id: str) -> Warehouse:
        stmt = select(Warehouse).where(Warehouse.warehouse_id == warehouse_id)
        stmt = await self._get_company_id_filter(stmt, company_id, Warehouse)
        return await self.session.scalar(stmt)


async def create_warehouse_repo(session: SessionDep) -> RepoWarehouse:
    return RepoWarehouse(session)


WarehouseRepoDep = Annotated[RepoWarehouse, Depends(create_warehouse_repo)]
