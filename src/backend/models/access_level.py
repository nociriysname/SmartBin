from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as POSTGRES_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.core.database.metadata import Base
from src.backend.core.enums import AccessLevel

__all__ = ("UserAccess",)


class UserAccess(Base, AsyncAttrs):
    __tablename__ = "access_level"

    id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("users.uuid", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    access_level: Mapped[AccessLevel] = mapped_column(
        Enum(AccessLevel),
        default=AccessLevel.employee,
        nullable=False,
    )

    warehouse_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("warehouses.warehouse_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    user = relationship("Users", back_populates="access_level")
    warehouse = relationship("Warehouse", back_populates="access_level")
