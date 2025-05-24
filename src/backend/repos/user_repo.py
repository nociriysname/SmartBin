from typing import Annotated, List, Optional, TypeVar

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, selectinload

from src.backend.core.database.async_engine import SessionDep
from src.backend.models.users import Users

__all__ = ("RepoUsers", "UsersReposDep")

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class RepoUsers:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_uuid(self, uuid: str, company_id: str) -> Optional[Users]:
        return await self.session.scalar(
            select(Users).filter(
                Users.uuid == uuid,
                Users.company_id == company_id,
            ),
        )

    async def get_by_number(
        self,
        phone_number: str,
        company_id: str,
    ) -> Optional[Users]:
        return await self.session.scalar(
            select(Users).filter(
                Users.number == phone_number,
                Users.company_id == company_id,
            ),
        )

    async def get_user_with_access(
        self,
        uuid: str,
        company_id: str,
    ) -> Optional[Users]:
        return await self.session.scalar(
            select(Users)
            .options(selectinload(Users.access))
            .filter(Users.uuid == uuid, Users.company_id == company_id),
        )

    async def create_user(self, user: Users) -> Users:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, uuid: str, company_id: str) -> None:
        user = await self.get_by_uuid(uuid, company_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()

    async def get_all(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Users], int]:
        query = (
            select(Users)
            .filter(Users.company_id == company_id)
            .limit(limit)
            .offset(offset)
        )
        users_result = await self.session.scalars(query)
        users = users_result.all()

        count_query = (
            select(func.count())
            .select_from(Users)
            .filter(Users.company_id == company_id)
        )
        total = await self.session.scalar(count_query)

        return users, total


async def create_user_repo(session: SessionDep) -> RepoUsers:
    return RepoUsers(session)


UsersReposDep = Annotated[RepoUsers, Depends(create_user_repo)]
