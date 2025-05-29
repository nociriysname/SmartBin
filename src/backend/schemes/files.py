from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.backend.core.enums import ProductType

__all__ = ("FileResponseDTO", "XLSProductDTO")


class FileResponseDTO(BaseModel):
    file_id: str = Field(description="Идентифатор файла")
    file_url: str = Field(description="URL файла Minio")
    file_type: str = Field(description="Тип файла(image, xls)")
    warehouse_id: str = Field(description="ID склада")
    uploaded_at: datetime = Field(description="Дата и время загрузки")


class XLSProductDTO(BaseModel):
    name: str = Field(max_length=255, description="Название продукта")
    cost: float = Field(gt=0, description="Стоимость продукта")
    article: str = Field(max_length=127, description="Артикул продукта")
    barcode: str = Field(max_length=255, description="Штрихкод продукта")
    item_type: ProductType = Field(..., description="Тип продукта")
    dekart_parameters: List[float] = Field(
        description="Картезианские параметры",
    )
    product_link: Optional[str] = Field(
        None,
        description="Ссылка на продукт",
    )

    @field_validator("dekart_parameters")
    def validate_dekart_parameters(cls, value: List[float]) -> List[float]:
        if not value:
            raise ValueError("Картезианские параметры не могут быть пустыми")

        return value
