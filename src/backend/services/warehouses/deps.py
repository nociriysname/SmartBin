from typing import Annotated

from fastapi import Depends

from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.repos.warehouses import WarehouseRepoDep
from src.backend.schemes.storage_objects import StorageResponseDTO

__all__ = ("WarehouseDep",)


async def get_warehouse(
        warehouse_id: str,
        company_id: str,
        warehouse_repo: WarehouseRepoDep,
) -> StorageResponseDTO:
    warehouse = await warehouse_repo.get_by_id(warehouse_id)
    if (warehouse.company_id != company_id) and (not warehouse):
        raise NotFoundError(f"Warehouse {warehouse_id} not found")

    return to_dto(warehouse, StorageResponseDTO)

WarehouseDep = Annotated[StorageResponseDTO, Depends(get_warehouse)]
