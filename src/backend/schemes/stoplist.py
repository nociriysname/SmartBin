from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.backend.core.enums import StopListReason

__all__ = ("StopListCreateDTO", "StopListUpdateDTO", "StopListResponseDTO")


class StopListCreateDTO(BaseModel):
    warehouse_id: str = Field(description="ID склада")
    product_id: str = Field(description="ID товара")
    reason: StopListReason = Field(
        description="Причина нахождения в стоп-листе",
    )


class StopListUpdateDTO(BaseModel):
    reason: Optional[StopListReason] = Field(
        None, description="Новая причина нахождения в стоп-листе",
    )


class StopListResponseDTO(BaseModel):
    warehouse_id: str = Field(description="ID склада")
    product_id: str = Field(description="ID товара")
    timestamp: datetime = Field(description="Время добавления в стоп-лист")
    reason: StopListReason = Field(
        description="Причина нахождения в стоп-листе",
    )

    model_config = ConfigDict(from_attributes=True)
