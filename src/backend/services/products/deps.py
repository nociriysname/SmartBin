from typing import Annotated

from fastapi import Depends

from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.core.utils.dto_refactor import to_dto
from src.backend.repos.products import ProductsRepoDep
from src.backend.schemes.item_list import ProductResponseDTO

__all__ = ("ProductDep",)


async def get_product(
    item_id: str,
    company_id: str,
    product_repo: ProductsRepoDep,
) -> ProductResponseDTO:
    product = await product_repo.get_by_id(item_id, company_id)
    if not product:
        raise NotFoundError(f"Product {item_id} not found")

    return to_dto(product, ProductResponseDTO)

ProductDep = Annotated[ProductResponseDTO, Depends(get_product)]
