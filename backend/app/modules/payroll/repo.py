from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_run(session: AsyncSession, run_id: UUID, lock: bool = False) -> dict[str, Any] | None:
    statement = "SELECT * FROM payroll_runs WHERE id = :run_id"
    if lock:
        statement += " FOR UPDATE"
    result = await session.execute(text(statement), {"run_id": run_id})
    row = result.mappings().one_or_none()
    if row is None:
        return None
    run = dict(row)
    slips = await session.execute(
        text("SELECT * FROM payslips WHERE run_id = :run_id ORDER BY employee_id"),
        {"run_id": run_id},
    )
    run["payslips"] = [dict(item) for item in slips.mappings().all()]
    return run


async def get_run_by_month(
    session: AsyncSession, month: date, lock: bool = False
) -> dict[str, Any] | None:
    statement = "SELECT * FROM payroll_runs WHERE month = :month"
    if lock:
        statement += " FOR UPDATE"
    result = await session.execute(text(statement), {"month": month})
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def create_run(session: AsyncSession, month: date, actor_id: UUID) -> dict[str, Any]:
    result = await session.execute(
        text(
            "INSERT INTO payroll_runs (month, created_by) VALUES (:month, :actor_id) "
            "ON CONFLICT (month) DO NOTHING RETURNING *"
        ),
        {"month": month, "actor_id": actor_id},
    )
    row = result.mappings().one_or_none()
    if row is not None:
        return dict(row)
    existing = await get_run_by_month(session, month, lock=True)
    return existing


async def replace_draft_payslips(
    session: AsyncSession, run_id: UUID, payslips: list[dict[str, Any]]
) -> None:
    await session.execute(text("DELETE FROM payslips WHERE run_id = :run_id"), {"run_id": run_id})
    if not payslips:
        return
    await session.execute(
        text(
            "INSERT INTO payslips (run_id, employee_id, basic, gross, working_days, "
            "absent_days, unpaid_days, half_days, deduction, tax, net) VALUES "
            "(:run_id, :employee_id, :basic, :gross, :working_days, :absent_days, "
            ":unpaid_days, :half_days, :deduction, :tax, :net)"
        ),
        [{"run_id": run_id, **item} for item in payslips],
    )


async def list_runs(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(text("SELECT * FROM payroll_runs ORDER BY month DESC"))
    runs = [dict(row) for row in result.mappings().all()]
    for run in runs:
        slips = await session.execute(
            text("SELECT * FROM payslips WHERE run_id = :run_id ORDER BY employee_id"),
            {"run_id": run["id"]},
        )
        run["payslips"] = [dict(item) for item in slips.mappings().all()]
    return runs


async def finalize_run(
    session: AsyncSession, run_id: UUID, actor_id: UUID
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            "UPDATE payroll_runs SET status = 'finalized', finalized_by = :actor_id, "
            "finalized_at = now() WHERE id = :run_id AND status = 'draft' RETURNING *"
        ),
        {"actor_id": actor_id, "run_id": run_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def list_payslips(
    session: AsyncSession, month: date | None, employee_id: UUID | None
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT p.* FROM payslips AS p JOIN payroll_runs AS r ON r.id = p.run_id "
            "WHERE (CAST(:month AS date) IS NULL OR r.month = CAST(:month AS date)) "
            "AND (CAST(:employee_id AS uuid) IS NULL OR p.employee_id = CAST(:employee_id AS uuid)) "
            "ORDER BY r.month DESC, p.employee_id"
        ),
        {"month": month, "employee_id": employee_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_payslip(session: AsyncSession, payslip_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            "SELECT p.*, r.month, "
            "jsonb_build_object('id', e.id, 'email', e.email, 'full_name', e.full_name, "
            "'code', e.code, 'department_id', e.department_id) AS employee, "
            "s.company_name "
            "FROM payslips AS p JOIN payroll_runs AS r ON r.id = p.run_id "
            "JOIN employees AS e ON e.id = p.employee_id "
            "CROSS JOIN settings AS s WHERE p.id = :payslip_id AND s.id = 1"
        ),
        {"payslip_id": payslip_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def get_run_recipients(
    session: AsyncSession, run_id: UUID
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT e.id AS employee_id, e.user_id "
            "FROM payslips AS p JOIN employees AS e ON e.id = p.employee_id "
            "WHERE p.run_id = :run_id AND e.user_id IS NOT NULL"
        ),
        {"run_id": run_id},
    )
    return [dict(row) for row in result.mappings().all()]
