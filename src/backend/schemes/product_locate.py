from pydantic import BaseModel, Field

__all__ = ("ProductLocationDTO", "ProductLocationResponseDTO")


class ProductLocationDTO(BaseModel):
    item_id: str = Field(description="ID товара")
    quantity: int = Field(gt=0, description="Кол-во")


class ProductLocationResponseDTO(BaseModel):
    storage_id: str = Field(description="ID стеллажа")
    message: str = Field(
        "Object has been located",
        description="Сообщение об успешной корректировке",
    )
    free_space_left: float = Field(description="Свободное место", ge=0)
