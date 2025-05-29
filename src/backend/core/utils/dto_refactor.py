from typing import Type, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncAttrs

T = TypeVar("T", bound=BaseModel)


def to_dto(model: AsyncAttrs, dto: Type[T]) -> T:
    if not model:
        raise ValueError("Model cannot be None")

    return dto(**{k: v for k, v, in model.__dict__.items()
                  if not k.startswith("_")})
