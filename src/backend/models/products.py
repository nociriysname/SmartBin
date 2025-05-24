from typing import Optional
from uuid import uuid4

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.core.database.metadata import Base
from src.backend.core.enums import ProductType

__all__ = ("Products",)


class Products(Base, AsyncAttrs):
    __tablename__ = "products"

    item_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )

    company_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    product_link: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    article: Mapped[str] = mapped_column(
        String(127),
        unique=True,
        nullable=False,
        index=True,
    )

    barcode: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    item_type: Mapped[ProductType] = mapped_column(
        Enum(ProductType),
        nullable=False,
    )

    dekart_parameters: Mapped[list[float] | None] = mapped_column(
        MutableList.as_mutable(ARRAY(Float)),
        nullable=False,
    )

    company = relationship("Companies", back_populates="products")
    storage = relationship("Storages", back_populates="items")
