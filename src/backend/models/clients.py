from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, func, String
from sqlalchemy.dialects.postgresql import UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.core.database.metadata import Base

__all__ = ("Companies",)


class Companies(Base, AsyncAttrs):
    __tablename__ = "companies"

    company_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )

    organization_name: Mapped[str] = mapped_column(
        String(127),
        unique=True,
        nullable=False,
        index=True,
    )

    owner_id: Mapped[Optional[str]] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    reg_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    activity: Mapped[bool] = mapped_column(default=True, nullable=False)

    users = relationship("Users", back_populates="company")
    warehouses = relationship(
        "Warehouse",
        back_populates="company",
        cascade="all,delete",
    )
    owner = relationship("Users", back_populates="owned_companies")
    products = relationship(
        "Products",
        back_populates="company",
        cascade="all,delete",
    )
    storages = relationship(
        "Storages",
        back_populates="company",
        cascade="all,delete",
    )
