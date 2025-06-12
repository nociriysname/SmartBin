from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import (
    ForbiddenError,
    NotFoundError,
    UniqueViolationError,
)
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.models.companies import Companies
from src.backend.repos.companies import CompanyRepoDep, RepoCompany
from src.backend.schemes.organization import (
    OrganizationModelDTO,
    OrganizationResponseDTO,
    OrganizationUpdateModelDTO,
)
from src.backend.services.users.deps import CEODep

__all__ = ("CompanyService", "CompanyServiceDep")


class CompanyService:
    def __init__(
        self,
        session: AsyncSession,
        company_repo: RepoCompany,
    ):
        self.session = session
        self.company_repo = company_repo

    async def create_company(
        self,
        user: CEODep,
        data: OrganizationModelDTO,
    ) -> OrganizationResponseDTO:
        existing_company = await self.company_repo.get_by_owner_id(user.uuid)
        if existing_company:
            raise ForbiddenError("User already owns a company")

        existing_name = await self.session.scalar(
            select(Companies).filter(
                Companies.organization_name == data.organization_name,
            ),
        )
        if existing_name:
            raise UniqueViolationError(
                f"Organization name {data.organization_name} already exists",
            )

        owner_id = data.owner_id if data.owner_id else user.uuid
        if owner_id != user.uuid:
            raise ForbiddenError("Only the current user can be set as owner")

        company = Companies(
            company_id=str(uuid4()),
            organization_name=data.organization_name,
            owner_id=owner_id,
            activity=True,
        )
        company = await self.company_repo.insert(company)
        return to_dto(company, OrganizationResponseDTO)

    async def delete_company(
        self,
        user: CEODep,
        company_id: str,
    ) -> None:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company {company_id} not found")

        if company.owner_id != user.uuid:
            raise ForbiddenError("User is not the owner of the company")

        await self.company_repo.delete(company_id)

    async def set_company_activity(
        self,
        user: CEODep,
        company_id: str,
        activity: bool,
    ) -> OrganizationResponseDTO:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company {company_id} not found")

        if company.owner_id != user.uuid:
            raise ForbiddenError("User is not the owner of the company")

        updated_company = await self.company_repo.update(
            company_id,
            activity=activity,
        )
        if not updated_company:
            raise NotFoundError(f"Company {company_id} not found")

        return to_dto(updated_company, OrganizationResponseDTO)

    async def update_company(
        self,
        user: CEODep,
        company_id: str,
        data: OrganizationUpdateModelDTO,
    ) -> OrganizationResponseDTO:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company {company_id} not found")

        if company.owner_id != user.uuid:
            raise ForbiddenError("User is not the owner of the company")

        update_data = {}
        if data.organization_name:
            existing_name = await self.session.scalar(
                select(Companies).filter(
                    Companies.organization_name == data.organization_name,
                ),
            )
            if existing_name and existing_name.company_id != company_id:
                raise UniqueViolationError(
                    f"Organization name {data.organization_name} "
                    f"already exists",
                )

            update_data["organization_name"] = data.organization_name

        if data.owner_id and data.owner_id != user.uuid:
            raise ForbiddenError("Only the current user can be set as owner")

        if data.activity is not None:
            update_data["activity"] = data.activity

        if update_data:
            updated_company = await self.company_repo.update(
                company_id,
                **update_data,
            )
            if not updated_company:
                raise NotFoundError(f"Company {company_id} not found")

            return to_dto(updated_company, OrganizationResponseDTO)

        return to_dto(company, OrganizationResponseDTO)


async def get_company_service(
    session: SessionDep,
    company_repo: CompanyRepoDep,
) -> CompanyService:
    return CompanyService(
        session=session,
        company_repo=company_repo,
    )

CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
