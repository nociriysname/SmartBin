from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, func, String
from sqlalchemy.dialects.postgresql import UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.core.database.metadata import Base

__all__ = ("Warehouse",)


class Warehouse(Base, AsyncAttrs):
    __tablename__ = "warehouses"

    company_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )

    warehouse_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    location: Mapped[str] = mapped_column(String(255), nullable=False)

    latitude: Mapped[float] = mapped_column(nullable=False)

    longitude: Mapped[float] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    companies = relationship("Companies", back_populates="warehouses")
    storages = relationship(
        "Storages",
        back_populates="warehouse",
        cascade="all,delete",
    )
    access = relationship("UserAccess", back_populates="warehouse")
