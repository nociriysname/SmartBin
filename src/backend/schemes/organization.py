from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


__all__ = (
    "OrganizationModelDTO",
    "OrganizationUpdateModelDTO",
    "OrganizationResponseDTO",
)


class OrganizationModelDTO(BaseModel):
    organization_name: str = Field(
        description="Название организации",
        max_length=127,
    )
    owner_id: Optional[str] = Field(
        None,
        description="ID Владельца организация",
    )


class OrganizationUpdateModelDTO(BaseModel):
    organization_name: str = Field(
        description="Название организации",
        max_length=127,
    )
    owner_id: Optional[str] = Field(
        None,
        description="ID Владельца организации",
    )
    activity: Optional[bool] = Field(
        None,
        description="Активна ли работа организация",
    )


class OrganizationResponseDTO(BaseModel):
    company_id: str = Field(description="ID организации")
    organization_name: str = Field(description="Название организации")
    owner_id: Optional[str] = Field(
        None,
        description="ID Владельца организации",
    )
    reg_date: datetime = Field(description="Дата регистрации организации")
    activity: bool = Field(description="Активна ли работа организация")

    model_config = ConfigDict(from_attributes=True)
