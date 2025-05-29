from typing import (Annotated,
                    Optional)

from fastapi import Depends
from sqlalchemy import (select,
                        update)
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.models.companies import Companies

__all__ = ("RepoCompany",
           "CompanyRepoDep")


class RepoCompany:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, company_id: str) -> Optional[Companies]:
        return await self.session.scalar(
            select(Companies).filter(Companies.company_id == company_id),
        )

    async def get_by_owner_id(self,
                              company_owner_id: str,
                              ) -> Optional[Companies]:
        return await self.session.scalar(
            select(Companies).filter(Companies.owner_id == company_owner_id),
        )

    async def insert(self,
                     company: Companies):
        self.session.add(company)
        await self.session.flush()
        await self.session.refresh(company)
        return company

    async def delete(self,
                     company_id: str) -> None:
        company = await self.get_by_id(company_id)
        await self.session.delete(company)
        await self.session.flush()

    async def update(self,
                     company_id: str,
                     organization_name: Optional[str] = None,
                     activity: Optional[bool] = None,
                     ) -> Optional[Companies]:
        company = await self.get_by_id(company_id)
        data = {}

        if organization_name:
            data["organization_name"] = organization_name

        if activity:
            data["activity"] = activity

        if data:
            await self.session.execute(
                update(Companies)
                .filter(Companies.company_id == company_id)
                .values(**data),
            )

            await self.session.flush()
            await self.session.refresh(company)

        return company


async def create_company_repo(session: SessionDep) -> RepoCompany:
    return RepoCompany(session)

CompanyRepoDep = Annotated[RepoCompany, Depends(create_company_repo)]
