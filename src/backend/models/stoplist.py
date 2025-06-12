from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM, UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.core.database.metadata import Base
from src.backend.core.enums import StopListReason


__all__ = ("StopList",)


class StopList(Base, AsyncAttrs):
    __tablename__ = "stop_list"

    warehouse_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("warehouses.warehouse_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    product_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )

    reason: Mapped[StopListReason] = mapped_column(
        ENUM(StopListReason, name="Stop list reason"),
        nullable=False,
    )

    product = relationship("Products", back_populates="stop_list")
    warehouse = relationship("Warehouses", back_populates="stop_list")
