from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import uuid4

from aioredis import Redis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.enums import AccessLevel
from src.backend.core.exc.exceptions.exceptions import (ForbiddenError,
                                                        NotFoundError,
                                                        UniqueViolationError)
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.core.utils.redis import get_redis_client
from src.backend.models.access_level import UserAccess
from src.backend.models.users import Users
from src.backend.repos.companies import CompanyRepoDep, RepoCompany
from src.backend.repos.storages import RepoStorage, StorageRepoDep
from src.backend.repos.users import RepoUsers, UsersReposDep
from src.backend.repos.warehouses import RepoWarehouse, WarehouseRepoDep
from src.backend.schemes.accessuserlevel import AccessUserLevelDTO
from src.backend.schemes.employee import (EmployeeCreateDTO,
                                          EmployeeResponseDTO,
                                          EmployeeUpdateDTO)
from src.backend.services.notifications.service import (NotificationService,
                                                        NotificationServiceDep)
from src.backend.services.users.deps import CEODep, RegManagerDep

__all__ = ("UserService",
           "UserServiceDep")


class UserService:
    def __init__(
            self,
            session: AsyncSession,
            user_repo: RepoUsers,
            company_repo: RepoCompany,
            storage_repo: RepoStorage,
            warehouse_repo: RepoWarehouse,
            notification_service: NotificationService,
            redis_client: Redis,
    ):
        self.session = session
        self.user_repo = user_repo
        self.company_repo = company_repo
        self.storage_repo = storage_repo
        self.warehouse_repo = warehouse_repo
        self.notification_service = notification_service
        self.redis_client = redis_client
        self.first_access_level = (AccessLevel.employee,
                                   AccessLevel.regional_manager,
                                   )
        self.second_access_level = (AccessLevel.regional_manager,
                                    AccessLevel.CEO,
                                    )

    async def create_user(
            self,
            creator: CEODep | RegManagerDep,
            company_id: str,
            data: EmployeeCreateDTO,
            access_level: AccessLevel,
            warehouse_id: Optional[str] = None,
    ) -> EmployeeResponseDTO:
        if access_level == AccessLevel.CEO \
                and creator.access_level != AccessLevel.CEO:
            raise ForbiddenError("Только CEO может назначать роль CEO")

        if access_level in self.first_access_level \
                and creator.access_level not in self.second_access_level:
            raise ForbiddenError("Недостаточно прав для создания пользователя")

        company = await self.company_repo.get_by_id(company_id)

        if not company:
            raise NotFoundError(f"Company {company_id} not found")

        if access_level in self.first_access_level and warehouse_id:
            warehouse = await self.storage_repo.get_by_id(warehouse_id)
            if (not warehouse) or (warehouse.company_id != company_id):
                raise NotFoundError(f"Warehouse {warehouse_id} not found")

        if await self.user_repo.check_exist_number(data.number):
            raise UniqueViolationError(
                f"User with number {data.number} already exists",
            )

        user = Users(
            uuid=str(uuid4()),
            name=data.name,
            number=data.number,
            company_id=company_id,
            firebase_token=None,
            reg_date=datetime.now(timezone.utc),
        )

        user = await self.user_repo.insert(user)

        if access_level != AccessLevel.CEO:
            access = UserAccess(
                id=user.uuid,
                warehouse_id=warehouse_id,
                access_level=access_level,
            )
            self.session.add(access)

        if access_level == AccessLevel.CEO:
            company.owner_id = user.uuid

        await self.session.flush()
        await self.session.refresh(user)
        await self.session.refresh(company)

        if user.firebase_token:
            await self.notification_service.send_notification(
                user_id=user.uuid,
                company_id=company.company_id,
                title="Welcome to SmartBin",
                body=f"Your account has been created, {user.name}",
            )

        return to_dto(user, EmployeeResponseDTO)

    async def update_user(
            self,
            creator: CEODep,
            user_id: str,
            company_id: str,
            data: EmployeeUpdateDTO,
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)

        if (user.company_id != company_id) or (not user):
            raise NotFoundError(f"User {user_id} not found")

        if data.name:
            user.name = data.name

        if data.number:
            if await self.user_repo.check_exist_number(data.number):
                raise UniqueViolationError(F"{data.number} exists")

            user.number = str(data.number)

        if data.company_id:
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                raise NotFoundError(f"Company {company_id} not found")

            user.company_id = company.company_id

        await self.session.flush()
        await self.session.refresh(user)

        async with self.redis_client as redis:
            await redis.delete(f"user:{user_id}")

    async def delete_user(
            self,
            creator: CEODep | RegManagerDep,
            user_id: str,
            company_id: str,
    ) -> bool:
        user = await self.user_repo.get_by_id(user_id)

        if (user.company_id != company_id) or (not user):
            raise NotFoundError(f"User {user_id} not found")

        await self.user_repo.delete(user)
        return True

    async def set_user_access(
            self,
            creator: CEODep | RegManagerDep,
            user_id: str,
            company_id: str,
            access: AccessUserLevelDTO,
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)

        if (user.company_id != company_id) or (not user):
            raise NotFoundError(f"User {user_id} not found")

        warehouse = await self.warehouse_repo.get_by_id(access.warehouse_id)

        if (warehouse.company_id != company_id) or (not warehouse):
            raise NotFoundError(f"Warehouse {access.warehouse_id} not found")

        access = UserAccess(
            id=user_id,
            warehouse_id=access.warehouse_id,
            access_level=access.access_level,
        )

        self.session.add(access)
        await self.session.flush()
        async with self.redis_client as redis:
            await redis.delete(
                f"access:{user_id}:{company_id}:{access.warehouse_id}")
            await redis.delete(f"user:{user_id}")


async def get_users_service(
        session: SessionDep,
        user_repo: UsersReposDep,
        company_repo: CompanyRepoDep,
        storage_repo: StorageRepoDep,
        warehouse_repo: WarehouseRepoDep,
        notification_service: NotificationServiceDep,
        redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> UserService:
    return UserService(
        session=session,
        user_repo=user_repo,
        company_repo=company_repo,
        storage_repo=storage_repo,
        warehouse_repo=warehouse_repo,
        notification_service=notification_service,
        redis_client=redis_client,
    )

UserServiceDep = Annotated[UserService, Depends(get_users_service)]
