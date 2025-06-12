from typing import Annotated, List, Optional, Tuple

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.models.products import Products

__all__ = ("RepoProducts", "ProductsRepoDep")


class RepoProducts:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
            self, item_id: str, company_id: str,
    ) -> Optional[Products]:
        return await self.session.scalar(
            select(Products).filter(
                Products.item_id == item_id,
                Products.company_id == company_id,
            ),
        )

    async def get_by_article(self, article: str) -> Optional[Products]:
        return await self.session.scalar(
            select(Products).filter(
                Products.article == article,
            ),
        )

    async def get_by_barcode(self, barcode: str) -> Optional[Products]:
        return await self.session.scalar(
            select(Products).filter(
                Products.barcode == barcode,
            ),
        )

    async def insert(self, product: Products) -> Products:
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def update(
            self, item_id: str, company_id: str, data: dict,
    ) -> Optional[Products]:
        await self.session.execute(
            update(Products).filter(
                Products.item_id == item_id,
                Products.company_id == company_id,
            ).values(**data),
        )
        return await self.get_by_id(item_id, company_id)

    async def delete(
            self, item_id: str, company_id: str,
    ) -> Optional[Products]:
        product = await self.get_by_id(item_id, company_id)
        if product:
            await self.session.delete(product)
            await self.session.flush()

    async def get_all(
            self,
            company_id: str,
            limit: int = 50,
            offset: int = 0,
    ) -> Tuple[List[Products], int]:
        query = (
            select(Products)
            .filter(Products.company_id == company_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(query)
        count_query = (
            select(func.count())
            .select_from(Products)
            .filter(Products.company_id == company_id)
        )
        total = await self.session.scalar(count_query)
        return list(result.all()), total


async def create_products_repo(session: SessionDep) -> RepoProducts:
    return RepoProducts(session)

ProductsRepoDep = Annotated[RepoProducts, Depends(create_products_repo)]
