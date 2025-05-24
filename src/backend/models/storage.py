from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.core.database.metadata import Base

__all__ = ("Storages",)


class Storages(Base, AsyncAttrs):
    __tablename__ = "storages"

    company_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    warehouse_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("warehouses.warehouse_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    storage_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )

    storage_id_list: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(POSTGRES_UUID)),
        nullable=False,
        default=[],
    )

    coordinates: Mapped[list[float]] = mapped_column(
        MutableList.as_mutable(ARRAY(Float)),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    company = relationship("Companies", back_populates="storages")
    warehouse = relationship("Warehouses", back_populates="storages")
    shelves = relationship(
        "Shelves",
        back_populates="storages",
        cascade="all,delete",
    )
