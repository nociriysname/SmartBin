from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.core.database.metadata import Base

__all__ = ("Shelves",)


class Shelves(Base, AsyncAttrs):
    __tablename__ = "shelves"

    storage_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("storages.storage_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    shelf_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )

    parameters: Mapped[list[float]] = mapped_column(
        MutableList.as_mutable(ARRAY(Float)),
        nullable=False,
        default=[],
    )

    shelves_parameters: Mapped[list[float]] = mapped_column(
        MutableList.as_mutable(ARRAY(Float)),
        nullable=False,
    )

    products_list: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(POSTGRES_UUID)),
        default=[],
        nullable=False,
    )

    space: Mapped[float] = mapped_column(Float, nullable=False)

    occupied_space: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    storage = relationship("Storages", back_populates="shelves")
    items = relationship("Products", back_populates="shelves")
