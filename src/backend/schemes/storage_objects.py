from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, computed_field, ConfigDict, Field

__all__ = ("StorageModelDTO", "StorageUpdateModelDTO", "StorageResponseDTO")


class StorageModelDTO(BaseModel):
    company_id: str = Field(description="ID организации")
    warehouse_id: str = Field(description="ID склада")
    location: str = Field(description="Локация", max_length=255)


class StorageUpdateModelDTO(StorageModelDTO):
    location: Optional[str] = Field(None, max_length=255)


class StorageResponseDTO(BaseModel):
    company_id: str = Field(description="ID организации")
    warehouse_id: str = Field(description="ID склада")
    location: str = Field(description="Локация склада")
    created_at: datetime = Field(description="Время создания стеллажа")
    storages: List[str] = Field(
        description="ID стеллажей",
        default_factory=list,
    )

    @computed_field
    def count_quantity(self) -> int:
        return len(self.storages)

    model_config = ConfigDict(from_attributes=True)
