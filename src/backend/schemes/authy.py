from pydantic import BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = (
    "AuthPushDTO",
    "AuthPushCodeDTO",
    "AuthPushRequestDTO",
    "AuthPushCodeTokenResponseDTO",
)


class AuthPushDTO(BaseModel):
    number: PhoneNumber = Field(description="Номер телефона")


class AuthPushRequestDTO(AuthPushDTO):
    pass


class AuthPushCodeDTO(AuthPushDTO):
    code: str = Field(
        min_length=6,
        max_length=6,
        description="Код подтверждения",
    )


class AuthPushCodeTokenResponseDTO(BaseModel):
    access_token: str = Field(description="JWT токен")
    token_type: str = Field("bearer", description="Тип?")
    expires_in: int = Field(60 * 5, description="Время истечения токена")
