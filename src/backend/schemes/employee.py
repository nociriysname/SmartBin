from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


__all__ = (
    "EmployeeModelDTO",
    "EmployeeCreateDTO",
    "EmployeeUpdateDTO",
    "EmployeeResponseDTO",
)


class EmployeeModelDTO(BaseModel):
    name: str = Field(description="Имя работника", max_length=63)
    number: PhoneNumber = Field(description="Номер телефона")


class EmployeeCreateDTO(EmployeeModelDTO):
    company_id: str


class EmployeeUpdateDTO(EmployeeModelDTO):
    name: Optional[str] = Field(
        None,
        description="Обновляемое имя",
        max_length=63,
    )
    number: Optional[PhoneNumber] = Field(
        None,
        description="Обновляемый номер",
    )
    company_id: Optional[str] = Field(None, description="Обновляемый ID")


class EmployeeResponseDTO(EmployeeModelDTO):
    uuid: str = Field(description="UUID")
    company_id: str = Field(description="ID компании")
    reg_date: datetime = Field(description="Дата регистрации компании")
    date_jwt_unactivate: Optional[datetime] = Field(
        None,
        description="Дата деактивации JWT",
    )

    @property
    def check_is_jwt_active(self) -> bool:
        return (
            datetime.now() < self.date_jwt_unactivate
            if self.date_jwt_unactivate
            else False
        )

    model_config = ConfigDict(from_attributes=True)
