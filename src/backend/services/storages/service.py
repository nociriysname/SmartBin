from datetime import datetime, timezone
import json
from typing import Annotated, Any, Dict, List, Optional, Union
from uuid import uuid4

from aioredis import Redis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import (BadRequestError,
                                                        ForbiddenError,
                                                        NotFoundError)
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.core.utils.redis import get_redis_client
from src.backend.models.shelves import Shelves
from src.backend.models.storage import Storages
from src.backend.repos.companies import CompanyRepoDep, RepoCompany
from src.backend.repos.storages import RepoStorage, StorageRepoDep
from src.backend.repos.users import RepoUsers, UsersReposDep
from src.backend.repos.warehouses import RepoWarehouse, WarehouseRepoDep
from src.backend.schemes.product_locate import (ProductLocationDTO,
                                                ProductLocationResponseDTO)
from src.backend.schemes.storage_settings import (
    StorageSettingsCreateDTO, StorageSettingsResponseDTO,
    StorageSettingsUpdateModelDTO)
from src.backend.services.auth.deps import AuthUserDep
from src.backend.services.users.deps import CEODep, RegManagerDep

__all__ = ("StorageService",
           "StorageServiceDep")


class StorageService:
    def __init__(
            self,
            session: AsyncSession,
            storage_repo: RepoStorage,
            company_repo: RepoCompany,
            user_repo: RepoUsers,
            warehouse_repo: RepoWarehouse,
            redis_client: Redis,
    ):
        self.session = session
        self.storage_repo = storage_repo
        self.company_repo = company_repo
        self.user_repo = user_repo
        self.warehouse_repo = warehouse_repo
        self.redis_client = redis_client

    async def check_access(
            self, user: AuthUserDep, warehouse_id: str, company_id: str,
    ) -> None:
        cache_key = f"access:{user.uuid}:{company_id}:{warehouse_id}"
        async with self.redis_client as redis:
            cached_access = await redis.get(cache_key)
            if cached_access == b"allowed":
                return

            if cached_access == b"denied":
                raise ForbiddenError("No access to warehouse")

        access_data = await self.user_repo.check_user_access_combined(
            user.uuid, company_id, warehouse_id)
        is_allowed = access_data["owner_id"] == user.uuid or access_data[
            "access_level"] == "regional_manager"
        async with self.redis_client as redis:
            await redis.setex(cache_key, 86400,
                              "allowed" if is_allowed else "denied")

        if not is_allowed:
            raise ForbiddenError("No access to warehouse")

    async def create_storage(
            self,
            user: Union[CEODep, RegManagerDep],
            data: StorageSettingsCreateDTO,
    ) -> StorageSettingsResponseDTO:
        if len(data.coordinates) != 4:
            raise BadRequestError(
                "Coordinates must have 4 values: [x1, y1, x2, y2]")

        warehouse = await self.warehouse_repo.get_by_id(data.warehouse_id)
        if not warehouse or warehouse.company_id != data.company_id:
            raise NotFoundError(f"Warehouse {data.warehouse_id} not found")

        storage = Storages(
            company_id=data.company_id,
            warehouse_id=data.warehouse_id,
            storage_id=str(uuid4()),
            coordinates=data.coordinates,
            storage_id_list=[],
            updated_at=datetime.now(timezone.utc),
        )
        storage = await self.storage_repo.insert_storage(storage)

        shelf = Shelves(
            storage_id=storage.storage_id,
            shelf_id=str(uuid4()),
            parameters=data.parameters,
            shelves_parameters=data.parameters,
            space=data.space,
            occupied_space=0.0,
            products_list=[],
            updated_at=datetime.now(timezone.utc),
        )
        shelf = await self.storage_repo.insert_shelf(shelf)
        storage.storage_id_list.append(shelf.shelf_id)

        await self.session.flush()
        await self.session.refresh(storage)
        return to_dto(storage, StorageSettingsResponseDTO)

    async def update_storage(
            self,
            user: Union[CEODep, RegManagerDep],
            storage_id: str,
            company_id: str,
            data: StorageSettingsUpdateModelDTO,
    ) -> StorageSettingsResponseDTO:
        storage = await self.storage_repo.get_by_id(storage_id)
        if not storage or storage.company_id != company_id:
            raise NotFoundError(f"Storage {storage_id} not found")

        if data.coordinates:
            if len(data.coordinates) != 4:
                raise BadRequestError(
                    "Coordinates must have 4 values: [x1, y1, x2, y2]")

            storage.coordinates = data.coordinates

        await self.session.flush()
        await self.session.refresh(storage)
        return to_dto(storage, StorageSettingsResponseDTO)

    async def delete_storage(
            self,
            user: Union[CEODep, RegManagerDep],
            storage_id: str,
            company_id: str,
    ) -> bool:
        storage = await self.storage_repo.get_by_id(storage_id)
        if not storage or storage.company_id != company_id:
            raise NotFoundError(f"Storage {storage_id} not found")

        await self.storage_repo.delete_storage(storage_id)
        return True

    async def duplicate_storage(
            self,
            user: Union[CEODep, RegManagerDep],
            storage_id: str,
            company_id: str,
            new_warehouse_id: Optional[str] = None,
    ) -> StorageSettingsResponseDTO:
        storage = await self.storage_repo.get_by_id(storage_id)
        if not storage or storage.company_id != company_id:
            raise NotFoundError(f"Storage {storage_id} not found")

        new_storage = Storages(
            company_id=company_id,
            warehouse_id=new_warehouse_id or storage.warehouse_id,
            storage_id=str(uuid4()),
            coordinates=list(storage.coordinates),
            storage_id_list=[],
            updated_at=datetime.now(timezone.utc),
        )
        new_storage = await self.storage_repo.insert_storage(new_storage)

        shelves = await self.storage_repo.get_shelves_by_storage(
            storage_id)
        for shelf in shelves:
            new_shelf = Shelves(
                storage_id=new_storage.storage_id,
                shelf_id=str(uuid4()),
                parameters=shelf.parameters,
                shelves_parameters=shelf.shelves_parameters,
                space=shelf.space,
                occupied_space=0.0,
                products_list=[],
                updated_at=datetime.now(timezone.utc),
            )
            new_shelf = await self.storage_repo.insert_shelf(new_shelf)
            new_storage.storage_id_list.append(new_shelf.shelf_id)

        await self.session.flush()
        await self.session.refresh(new_storage)
        return to_dto(new_storage, StorageSettingsResponseDTO)

    async def check_crowded_shelves(
            self,
            user: AuthUserDep,
            company_id: str,
            threshold: float = 0.9,
    ) -> List[Dict[str, Any]]:
        shelves = await self.storage_repo.get_shelves_by_company(company_id)
        crowded = []
        for shelf in shelves:
            if shelf.occupied_space / shelf.space >= threshold:
                crowded.append({
                    "shelf_id": shelf.shelf_id,
                    "storage_id": shelf.storage_id,
                    "occupied_space": shelf.occupied_space,
                    "space": shelf.space,
                    "fill_percentage":
                        shelf.occupied_space / shelf.space * 100,
                })

        return crowded

    async def get_storage_layout(
            self,
            user: AuthUserDep,
            company_id: str,
            warehouse_id: str,
    ) -> Dict[str, Any]:
        cache_key = f"layout:{warehouse_id}"
        async with self.redis_client as redis:
            cached_layout = await redis.get(cache_key)
            if cached_layout:
                return json.loads(cached_layout)

        storages = await self.storage_repo.get_storage_by_warehouse(
            warehouse_id, company_id,
        )

        storages_data = []

        if not storages:
            raise BadRequestError("No storages found")

        for storage in storages:
            shelves_in_storage = \
                await self.storage_repo.get_shelves_by_storage(
                    storage.storage_id,
                )
            shelf_list = [
                {
                    "shelf_id": shelf.shelf_id,
                    "parameters": shelf.parameters,
                    "occupied_space": shelf.occupied_space,
                    "space": shelf.space,
                    "products": shelf.products_list,
                }
                for shelf in shelves_in_storage
            ]

            storages_data.append({
                "storage_id": storage.storage_id,
                "coordinates": storage.coordinates,
                "shelves": shelf_list,
            })

        layout = {"storages": storages_data}

        async with self.redis_client as redis:
            await redis.setex(cache_key, 3600, json.dumps(layout))

        return layout

    async def add_product_to_shelf(
            self,
            user: Union[CEODep, RegManagerDep],
            storage_id: str,
            company_id: str,
            data: ProductLocationDTO,
    ) -> ProductLocationResponseDTO:
        storage = await self.storage_repo.get_by_id(storage_id)
        if not storage or storage.company_id != company_id:
            raise NotFoundError(f"Storage {storage_id} not found")

        product = await self.storage_repo.get_product_by_id(data.item_id)
        if not product:
            raise NotFoundError(f"Product {data.item_id} not found")

        shelves = await self.storage_repo.get_shelves_by_storage(
            storage_id)
        if not shelves:
            raise NotFoundError(
                f"Shelves for storage {storage_id} not found")

        for shelf in shelves:
            volume = product.dekart_parameters[0] * data.quantity

            if shelf.occupied_space + volume <= shelf.space:
                shelf.occupied_space += volume
                shelf.products_list.append(data.item_id)
                await self.session.flush()
                return ProductLocationResponseDTO(
                    storage_id=storage_id,
                    message="Product placed successfully",
                    free_space_left=shelf.space - shelf.occupied_space,
                )

        raise BadRequestError("No free space on shelves")


async def get_storage_service(
        session: SessionDep,
        storage_repo: StorageRepoDep,
        company_repo: CompanyRepoDep,
        user_repo: UsersReposDep,
        warehouse_repo: WarehouseRepoDep,
        redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> StorageService:
    return StorageService(
        session=session,
        storage_repo=storage_repo,
        company_repo=company_repo,
        user_repo=user_repo,
        warehouse_repo=warehouse_repo,
        redis_client=redis_client,
    )

StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]
