from datetime import date
from typing import List

from sqlalchemy import Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as POSTGRES_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.core.database.metadata import Base

__all__ = ("Report",)


class Report(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )

    warehouse_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("warehouses.warehouse_id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id: Mapped[str] = mapped_column(
        POSTGRES_UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    actions: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=[],
    )
