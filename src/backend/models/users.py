from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, func, String
from sqlalchemy.dialects.postgresql import UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.core.database.metadata import Base

__all__ = ("Users",)


class Users(Base, AsyncAttrs):
    __tablename__ = "users"

    uuid: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(String(63), nullable=False)

    number: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
        unique=True,
    )

    company_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )

    reg_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    firebase_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    date_jwt_unactivate: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    company = relationship("Company", back_populates="users")
    access = relationship(
        "UserAccess",
        back_populates="user",
        cascade="all,delete",
    )
