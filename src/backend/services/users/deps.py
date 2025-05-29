from typing import Annotated

from fastapi import Depends

from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.models.users import Users
from src.backend.repos.users import UsersReposDep
from src.backend.schemes.employee import EmployeeResponseDTO
from src.backend.services.auth.deps import AuthUserDep

__all__ = ("UserDTO",
           "CEODep",
           "RegManagerDep")


async def get_user_dto(
        user_id: str,
        company_id: str,
        user_repo: UsersReposDep,
) -> EmployeeResponseDTO:
    user = await user_repo.get_by_id(user_id)
    if (user.company_id != company_id) or (not user):
        raise NotFoundError(f"User {user_id} not found")

    return to_dto(user, EmployeeResponseDTO)


async def get_ceo_user(
        user: AuthUserDep,
        company_id: str,
        user_repo: UsersReposDep,
) -> Users:
    company = await user_repo.get_by_id(company_id)
    if (not company) or (company.owner_id != user.uuid):
        raise NotFoundError(f"User {user.uuid} not found")

    return user


async def get_regional_manager(
        user: AuthUserDep,
        company_id: str,
        warehouse_id: str,
        user_repo: UsersReposDep,
) -> Users:
    access = await user_repo.get_user_access(user.uuid, warehouse_id)
    if (access.access_level != "regional_manager") or (not access):
        raise NotFoundError(f"User {user.uuid} not found")

    if user.company_id != company_id:
        raise NotFoundError(
            f"User {user.uuid} not lead in company {company_id}",
        )

    return user

UserDTO = Annotated[EmployeeResponseDTO, Depends(get_user_dto)]
CEODep = Annotated[Users, Depends(get_ceo_user)]
RegManagerDep = Annotated[Users, Depends(get_regional_manager)]
