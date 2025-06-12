from typing import Annotated, List, Tuple
from uuid import uuid4

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import (
    BadRequestError, NotFoundError, UniqueViolationError,
)
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.models.products import Products
from src.backend.repos.companies import CompanyRepoDep, RepoCompany
from src.backend.repos.products import ProductsRepoDep, RepoProducts
from src.backend.schemes.files import FileResponseDTO, XLSProductDTO
from src.backend.schemes.item_list import (
    ProductCreateDTO, ProductResponseDTO, ProductUpdateDTO,
)
from src.backend.services.files.service import (
    FilesService, FilesServiceDep,
)
from src.backend.services.users.deps import CEODep
from src.backend.services.warehouses.deps import WarehouseDep

__all__ = ("ProductService", "ProductServiceDep")


class ProductService:
    def __init__(
        self,
        session: AsyncSession,
        product_repo: RepoProducts,
        company_repo: RepoCompany,
        files_service: FilesService,
    ):
        self.session = session
        self.product_repo = product_repo
        self.company_repo = company_repo
        self.files_service = files_service

    async def get_product(
            self,
            user: CEODep,
            company_id: str,
            item_id: str,
    ) -> ProductResponseDTO:
        company = await self.company_repo.get_by_id(company_id)
        if (company.owner_id != user.uuid) or (not company):
            raise NotFoundError("Company not found/access denied")

        product = await self.product_repo.get_by_id(item_id, company_id)
        if not product:
            raise NotFoundError(f"Product {item_id} not found")

        return to_dto(product, ProductResponseDTO)

    async def get_all_products(
            self,
            user: CEODep,
            company_id: str,
            limit: int,
            offset: int,
    ) -> Tuple[List[ProductResponseDTO], int]:
        company = await self.company_repo.get_by_id(company_id)
        if not company or company.owner_id != user.uuid:
            raise NotFoundError(
                f"Company {company_id} not found or access denied")

        products, total = await self.product_repo.get_all(company_id, limit,
                                                          offset)
        return [to_dto(product, ProductResponseDTO) for product in
                products], total

    async def create_product(
            self,
            user: CEODep,
            company_id: str,
            data: ProductCreateDTO,
    ) -> ProductResponseDTO:
        company = await self.company_repo.get_by_id(company_id)
        if not company or company.owner_id != user.uuid:
            raise NotFoundError(
                f"Company {company_id} not found or access denied")

        if await self.product_repo.get_by_article(data.article):
            raise UniqueViolationError(
                f"Article {data.article} already exists")

        if await self.product_repo.get_by_barcode(data.barcode):
            raise UniqueViolationError(
                f"Barcode {data.barcode} already exists")

        product = Products(
            item_id=str(uuid4()),
            company_id=company_id,
            name=data.name,
            cost=data.cost,
            product_link=data.product_link,
            article=data.article,
            barcode=data.barcode,
            item_type=data.item_type,
            dekart_parameters=data.dekart_parameters,
        )
        product = await self.product_repo.insert(product)
        return to_dto(product, ProductResponseDTO)

    async def update_product(
            self,
            user: CEODep,
            company_id: str,
            item_id: str,
            data: ProductUpdateDTO,
    ) -> ProductResponseDTO:
        company = await self.company_repo.get_by_id(company_id)
        if not company or company.owner_id != user.uuid:
            raise NotFoundError(
                f"Company {company_id} not found or access denied")

        product = await self.product_repo.get_by_id(item_id, company_id)
        if not product:
            raise NotFoundError(f"Product {item_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if "article" in update_data:
            existing = await self.product_repo.get_by_article(
                update_data["article"])
            if existing and existing.item_id != item_id:
                raise UniqueViolationError(
                    f"Article {update_data['article']} already exists")

        if "barcode" in update_data:
            existing = await self.product_repo.get_by_barcode(
                update_data["barcode"])
            if existing and existing.item_id != item_id:
                raise UniqueViolationError(
                    f"Barcode {update_data['barcode']} already exists")

        updated_product = await self.product_repo.update(item_id, company_id,
                                                         update_data)
        if not updated_product:
            raise NotFoundError(f"Product {item_id} not found")

        return to_dto(updated_product, ProductResponseDTO)

    async def delete_product(
            self,
            user: CEODep,
            company_id: str,
            item_id: str,
    ) -> None:
        company = await self.company_repo.get_by_id(company_id)
        if not company or company.owner_id != user.uuid:
            raise NotFoundError(
                f"Company {company_id} not found or access denied")

        product = await self.product_repo.get_by_id(item_id, company_id)
        if not product:
            raise NotFoundError(f"Product {item_id} not found")

        await self.product_repo.delete(item_id, company_id)

    async def upload_products_xls(
            self,
            user: CEODep,
            warehouse: WarehouseDep,
            company_id: str,
            file: UploadFile,
            products: List[XLSProductDTO],
    ) -> Tuple[FileResponseDTO, List[ProductResponseDTO]]:
        company = await self.company_repo.get_by_id(company_id)
        if not company or company.owner_id != user.uuid:
            raise NotFoundError(
                f"Company {company_id} not found or access denied")

        if warehouse.company_id != company_id:
            raise BadRequestError("Warehouse does not belong to the company")

        file_response, _ = await self.files_service.upload_product_xls(
            user,
            warehouse,
            company_id,
            file,
            products,
        )
        created_products = []
        for product_data in products:
            if await self.product_repo.get_by_article(product_data.article):
                raise UniqueViolationError(
                    f"Article {product_data.article} already exists")

            if await self.product_repo.get_by_barcode(product_data.barcode):
                raise UniqueViolationError(
                    f"Barcode {product_data.barcode} already exists")

            product = Products(
                item_id=str(uuid4()),
                company_id=company_id,
                name=product_data.name,
                cost=product_data.cost,
                product_link=product_data.product_link,
                article=product_data.article,
                barcode=product_data.barcode,
                item_type=product_data.item_type,
                dekart_parameters=product_data.dekart_parameters,
            )

            product = await self.product_repo.insert(product)

            created_products.append(
                to_dto(product, ProductResponseDTO),
            )

        return file_response, created_products


async def get_product_service(
        session: SessionDep,
        product_repo: ProductsRepoDep,
        company_repo: CompanyRepoDep,
        files_service: FilesServiceDep,
) -> ProductService:
    return ProductService(
        session=session,
        product_repo=product_repo,
        company_repo=company_repo,
        files_service=files_service,
    )


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
