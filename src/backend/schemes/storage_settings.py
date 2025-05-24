from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    computed_field,
    ConfigDict,
    Field,
    model_validator,
)

__all__ = (
    "StorageSettingsCreateDTO",
    "StorageSettingsResponseDTO",
    "StorageSettingsModelDTO",
    "StorageSettingsUpdateModelDTO",
)


class StorageSettingsModelDTO(BaseModel):
    coordinates: List[float] = Field(
        description="Координаты ограничения формата (x1,y1,x2,y2)",
    )
    parameters: List[float] = Field(
        description="Параметры - length,width,height",
    )
    space: float = Field(description="Объем", gt=0)


class StorageSettingsCreateDTO(StorageSettingsModelDTO):
    company_id: str
    warehouse_id: str


class StorageSettingsUpdateModelDTO(BaseModel):
    coordinates: Optional[List[float]] = Field(
        description="Координаты ограничения формата (x1,y1,x2,y2)",
    )
    parameters: Optional[List[float]] = Field(
        description="Параметры формата (length,width,height)",
    )
    space: Optional[float] = None
    occupied_space: Optional[float] = None
    products_list: Optional[List[str]] = None


class StorageSettingsResponseDTO(BaseModel):
    company_id: str = Field(description="ID организации")
    warehouse_id: str = Field(description="ID склада")
    storage_id: str = Field(description="ID стеллажа")
    occupied_space: float = Field(description="Занятое место")
    products_list: List[str] = Field(
        description="Список товаров на стеллаже по их ID",
    )
    updated_at: datetime = Field(description="Последнее обновление")

    @model_validator(mode="after")
    def check_occupied_space(self):
        if self.occupied_space > self.space:
            raise ValueError("Occupied space can't exceeded main space")

        return self

    @computed_field
    def free_space(self) -> float:
        return self.space - self.occupied_space

    model_config = ConfigDict(from_attributes=True)
