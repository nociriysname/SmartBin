from functools import reduce
from typing import List, Optional

from pydantic import (
    BaseModel,
    computed_field,
    ConfigDict,
    Field,
    model_validator,
)

from src.backend.core.enums import ProductType

__all__ = (
    "ProductModelDTO",
    "ProductCreateDTO",
    "ProductUpdateDTO",
    "ProductResponseDTO",
)


class ProductModelDTO(BaseModel):
    name: str = Field(description="Название товара", max_length=255)
    cost: float = Field(description="Цена товара", gt=0)
    article: str = Field(description="Артикул товара", max_length=127)
    barcode: str = Field(description="Штрих/Баркод товара", max_length=255)
    item_type: ProductType = Field(description="Тип товара-boxed/unboxed")
    dekart_parameters: Optional[List[float]] = Field(
        None,
        description="Параметры товара",
    )

    @model_validator(mode="after")
    def validate_params(self):
        if self.item_type == "unboxed" and self.dekart_parameters:
            raise ValueError("Dekart_parameters is None for not_box objects")

        if self.item_type == "boxed" and (not self.dekart_parameters):
            raise ValueError("Dekart_parameters in not None fox box objects")

        return self


class ProductCreateDTO(ProductModelDTO):
    company_id: str = Field(description="ID компании")


class ProductUpdateDTO(BaseModel):
    name: Optional[str] = Field(
        None,
        description="Обновляем. название товара",
        max_length=255,
    )
    cost: Optional[float] = Field(
        None,
        description="Обновляем. цена товара",
        gt=0,
    )
    article: Optional[str] = Field(
        None,
        description="Обновляем. артикул товара",
        max_length=127,
    )
    barcode: Optional[str] = Field(
        None,
        description="Обновляем. штрих/баркод товара",
        max_length=255,
    )
    item_type: Optional[ProductType] = Field(
        None,
        description="Обновляем. тип товара-boxed/unboxed",
    )
    dekart_parameters: Optional[List[float]] = Field(
        None,
        description="Обновляем. параметры товара",
    )


class ProductResponseDTO(ProductModelDTO):
    item_id: str = Field(description="Уникальный ID товара")
    company_id: str = Field(description="ID компании")

    @computed_field
    def finding_volume(self) -> float:
        return (
            reduce(lambda x, y: x * y, self.dekart_parameters or [0, 0, 0], 1)
            if self.dekart_parameters
            else 0
        )

    # вообще по логике должно составиться выражение
    # (1*width)*(1*height)*(1*length),или (((1*width)*height)*length)

    model_config = ConfigDict(from_attributes=True)
