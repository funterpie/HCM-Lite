from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.errors import AppError
from app.core.notify import notify
from app.modules.attendance.service import payroll_inputs
from app.modules.payroll import repo
from app.rules.payroll import compute_payslip


async def create_or_recalculate_run(
    session: AsyncSession, actor_id: UUID, month: date
) -> dict[str, Any]:
    existing_run = await repo.get_run_by_month(session, month, lock=True)
    run = await repo.create_run(session, month, actor_id)
    if run is None:
        await session.rollback()
        raise AppError(409, "payroll_run_conflict", "The payroll run could not be locked.")
    if run["status"] == "finalized":
        await session.rollback()
        raise AppError(409, "run_finalized", "A finalized payroll run cannot be changed.")

    inputs = await payroll_inputs(session, month)
    slips: list[dict[str, Any]] = []
    for payroll_input in inputs:
        try:
            calculation = compute_payslip(
                basic=payroll_input["basic_salary"],
                join_date=payroll_input["join_date"],
                exit_date=payroll_input["exit_date"],
                month=month,
                working_days_in_month=payroll_input["working_days_in_month"],
                payable_working_days=payroll_input["payable_working_days"],
                absent_days=payroll_input["absent_days"],
                unpaid_days=payroll_input["unpaid_days"],
                half_days=payroll_input["half_days"],
            )
        except ValueError as exc:
            await session.rollback()
            raise AppError(422, "payroll_calculation_invalid", str(exc)) from exc
        slips.append({"employee_id": payroll_input["employee_id"], **calculation})

    await repo.replace_draft_payslips(session, run["id"], slips)
    updated = await repo.get_run(session, run["id"])
    await audit_log(
        session,
        actor_id,
        "recalculate" if existing_run else "create",
        "payroll_run",
        run["id"],
        run,
        updated,
    )
    await session.commit()
    return {"data": updated}


async def list_runs(session: AsyncSession) -> dict[str, Any]:
    return {"data": await repo.list_runs(session)}


async def get_run(session: AsyncSession, run_id: UUID) -> dict[str, Any]:
    run = await repo.get_run(session, run_id)
    if run is None:
        raise AppError(404, "payroll_run_not_found", "The payroll run was not found.")
    return {"data": run}


async def finalize_payroll_run(
    session: AsyncSession, actor_id: UUID, run_id: UUID
) -> dict[str, Any]:
    before = await repo.get_run(session, run_id, lock=True)
    if before is None:
        raise AppError(404, "payroll_run_not_found", "The payroll run was not found.")
    if before["status"] == "finalized":
        await session.rollback()
        raise AppError(409, "run_finalized", "The payroll run is already finalized.")
    finalized = await repo.finalize_run(session, run_id, actor_id)
    if finalized is None:
        await session.rollback()
        raise AppError(409, "run_finalized", "The payroll run is already finalized.")

    for recipient in await repo.get_run_recipients(session, run_id):
        await notify(
            session,
            recipient["user_id"],
            f"Payslip ready for {finalized['month']:%B %Y}",
            "Your payslip is ready to view.",
        )
    after = await repo.get_run(session, run_id)
    await audit_log(session, actor_id, "finalize", "payroll_run", run_id, before, after)
    await session.commit()
    return {"data": after}


async def list_payslips(
    session: AsyncSession, month: date | None, employee_id: UUID | None
) -> dict[str, Any]:
    return {"data": await repo.list_payslips(session, month, employee_id)}


async def get_payslip(session: AsyncSession, payslip_id: UUID) -> dict[str, Any]:
    payslip = await repo.get_payslip(session, payslip_id)
    if payslip is None:
        raise AppError(404, "payslip_not_found", "The payslip was not found.")
    return payslip
