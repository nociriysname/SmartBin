from typing import Annotated, List, Optional

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.core.database.async_engine import SessionDep
from src.backend.models.users import Users

__all__ = ("RepoUsers", "UsersReposDep")


class RepoUsers:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, uuid: str) -> Optional[Users]:
        return await self.session.scalar(
            select(Users).filter(
                Users.uuid == uuid,
            ),
        )

    async def get_by_number(
        self,
        phone_number: str,
    ) -> Optional[Users]:
        return await self.session.scalar(
            select(Users).filter(
                Users.number == phone_number,
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

    async def get_by_auth(
        self,
        number: str,
        firebase_token: str,
    ) -> Optional[Users]:
        return await self.session.scalar(
            select(Users).filter(
                Users.number == number, Users.firebase_token == firebase_token,
            ),
        )

    async def check_exist_number(self, number: str) -> bool:
        return await self.session.scalar(
            select(True).where(
                Users.number == number,
                Users.firebase_token.isnot(None),
            ),
        ) or False

    async def insert(
        self,
        number: str,
        firebase_token: Optional[str],
        name: str,
        company_id: str,
    ) -> Users:
        user = Users(
            number=number,
            name=name,
            firebase_token=firebase_token,
            company_id=company_id,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, uuid: str) -> None:
        user = await self.get_by_id(uuid)
        await self.session.delete(user)
        await self.session.flush()

    async def update_token_by_id(
        self,
        user_id: str,
        firebase_token: Optional[str],
    ) -> None:
        await self.session.execute(
            update(Users)
            .filter(Users.uuid == user_id)
            .values(firebase_token=firebase_token),
        )
        await self.session.flush()

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

        count_query = (
            select(func.count())
            .select_from(Users)
            .filter(Users.company_id == company_id)
        )
        total = await self.session.scalar(count_query)

        return list(users_result.all()), total


async def create_user_repo(session: SessionDep) -> RepoUsers:
    return RepoUsers(session)


UsersReposDep = Annotated[RepoUsers, Depends(create_user_repo)]
