from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.backend.core.enums import AccessLevel

__all__ = (
    "AccessUserLevelDTO",
    "AccessUserLevelUpdateDTO",
    "AccessUserLevelResponseDTO",
)


class AccessUserLevelDTO(BaseModel):
    id: str
    warehouse_id: str
    access_level: AccessLevel


class AccessUserLevelUpdateDTO(AccessUserLevelDTO):
    access_level: Optional[AccessLevel] = None


class AccessUserLevelResponseDTO(BaseModel):
    id: str
    warehouse_id: str
    access_level: AccessLevel

    model_config = ConfigDict(from_attributes=True)
