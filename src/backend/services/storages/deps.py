from typing import Annotated

from fastapi import Depends

from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.repos.storages import StorageRepoDep
from src.backend.schemes.storage_settings import StorageSettingsResponseDTO
from src.backend.services.auth.deps import AuthUserDep
from src.backend.services.storages.service import StorageServiceDep

__all__ = ("StorageDep", "StorageAccessDep")


async def get_storage(
    storage_id: str,
    company_id: str,
    storage_repo: StorageRepoDep,
) -> StorageSettingsResponseDTO:
    storage = await storage_repo.get_by_id(storage_id)
    if not storage or storage.company_id != company_id:
        raise NotFoundError(f"Стеллаж {storage_id} не найден")

    return to_dto(storage, StorageSettingsResponseDTO)


async def check_storage_access(
    user: AuthUserDep,
    company_id: str,
    warehouse_id: str,
    storage_service: StorageServiceDep,
) -> AuthUserDep:
    await storage_service.check_access(user, warehouse_id, company_id)
    return user

StorageDep = Annotated[StorageSettingsResponseDTO, Depends(get_storage)]
StorageAccessDep = Annotated[AuthUserDep, Depends(check_storage_access)]
