from datetime import date
from typing import Annotated, Any, Dict

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.models.report import Report
from src.backend.repos.warehouses import RepoWarehouse, WarehouseRepoDep

__all__ = ("ReportService", "ReportServiceDep")


class ReportService:
    def __init__(self, session: AsyncSession, warehouse_repo: RepoWarehouse):
        self.session = session
        self.warehouse_repo = warehouse_repo

    async def log_action(
            self,
            product_id: str,
            warehouse_id: str,
            action: str,
            quantity: int = 1) -> None:
        today = date.today()
        report = await self.session.scalar(
            select(Report).filter(
                Report.warehouse_id == str(warehouse_id),
                Report.date == today,
            ),
        )
        company_id = await self.warehouse_repo.get_by_id(warehouse_id)
        company_id = str(company_id.company_id)
        if not report:
            report = Report(
                warehouse_id=str(warehouse_id),
                company_id=company_id,
                date=today,
                actions=[],
            )
            self.session.add(report)

        action_entry = {
            "product_id": str(product_id),
            "action": action,
            "quantity": quantity,
        }
        report.actions.append(action_entry)
        await self.session.flush()

    async def get_daily_report(
            self, warehouse_id: str, report_date: date,
    ) -> Dict[str, Any]:
        report = await self.session.scalar(
            select(Report).filter(
                Report.warehouse_id == str(warehouse_id),
                Report.date == report_date,
            ),
        )
        if not report:
            raise NotFoundError(f"Report in {report_date} not found")

        return {
            "warehouse_id": report.warehouse_id,
            "date": report.date,
            "actions": report.actions,
        }


async def get_report_service(
        session: SessionDep,
        warehouse_repo: WarehouseRepoDep,
) -> ReportService:
    return ReportService(
        session=session,
        warehouse_repo=warehouse_repo,
    )


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
