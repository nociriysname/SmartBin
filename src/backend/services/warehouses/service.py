from datetime import datetime, timezone
from typing import Annotated, Union
from uuid import uuid4

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.enums import AccessLevel
from src.backend.core.exc.exceptions.exceptions import (ForbiddenError,
                                                        NotFoundError)
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.models.warehouses import Warehouse
from src.backend.repos.companies import CompanyRepoDep, RepoCompany
from src.backend.repos.users import RepoUsers, UsersReposDep
from src.backend.repos.warehouses import RepoWarehouse, WarehouseRepoDep
from src.backend.schemes.storage_objects import (StorageModelDTO,
                                                 StorageResponseDTO)
from src.backend.services.auth.deps import AuthUserDep
from src.backend.services.users.deps import CEODep, RegManagerDep

__all__ = ("WarehouseService",
           "WarehouseServiceDep")


class WarehouseService:
    def __init__(
        self,
        session: AsyncSession,
        warehouse_repo: RepoWarehouse,
        company_repo: RepoCompany,
        user_repo: RepoUsers,
    ):
        self.session = session
        self.warehouse_repo = warehouse_repo
        self.company_repo = company_repo
        self.user_repo = user_repo

    async def get_warehouse(
        self,
        user: AuthUserDep,
        company_id: str,
        warehouse_id: str,
    ) -> StorageResponseDTO:

        warehouse = await self.warehouse_repo.get_by_id(warehouse_id)
        if not (warehouse.company_id != company_id) or (not warehouse):
            raise NotFoundError(f"Warehouse {warehouse_id} not found")

        access = await self.user_repo.get_user_access(user.uuid, company_id)
        if (user.access_level != AccessLevel.CEO) and (not access):
            raise ForbiddenError("User have no permission")

        return to_dto(warehouse, StorageResponseDTO)

    async def create_warehouse(
        self,
        user: CEODep,
        company_id: str,
        data: StorageModelDTO,
    ) -> StorageResponseDTO:
        company = await self.company_repo.get_by_id(company_id)

        if (company.owner_id != user.access) or (not company):
            raise NotFoundError(f"Company {company_id} not found")

        warehouse = Warehouse(
            warehouse_id=str(uuid4()),
            company_id=company_id,
            location=data.location,
            latitude=data.latitude,
            longitude=data.longitude,
            created_at=datetime.now(timezone.utc),
        )
        warehouse = await self.warehouse_repo.insert(warehouse)

        return to_dto(warehouse, StorageResponseDTO)

    async def delete_warehouse(
        self,
        user: CEODep,
        company_id: str,
        warehouse_id: str,
    ) -> bool:
        warehouse = await self.warehouse_repo.delete(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")

        return True

    async def update_warehouse(
        self,
        user: Union[CEODep, RegManagerDep],
        company_id: str,
        warehouse_id: str,
        data: StorageModelDTO,
    ) -> StorageResponseDTO:
        warehouse = await self.warehouse_repo.update(
            warehouse_id,
            location=data.location,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")

        return to_dto(warehouse, StorageResponseDTO)


async def get_warehouse_service(
        session: AsyncSession,
        warehouse_repo: WarehouseRepoDep,
        company_repo: CompanyRepoDep,
        user_repo: UsersReposDep,
) -> WarehouseService:
    return WarehouseService(
        session=session,
        warehouse_repo=warehouse_repo,
        company_repo=company_repo,
        user_repo=user_repo,
    )

WarehouseServiceDep = Annotated[
    WarehouseService, Depends(get_warehouse_service),
]
