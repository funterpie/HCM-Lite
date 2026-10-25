from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, current_user, require_role
from app.core.errors import AppError
from app.db import get_session
from app.modules.payroll import service
from app.modules.payroll.schemas import (
    PayrollRunCreate,
    PayrollRunListResponse,
    PayrollRunResponse,
    PayslipListResponse,
)
from app.modules.payroll.pdf import build_payslip_pdf_bytes

router = APIRouter(prefix="/payroll", tags=["payroll"])
payslip_pdf_router = APIRouter(prefix="/payslips", tags=["payroll"])


@router.post("/runs", response_model=PayrollRunResponse, status_code=status.HTTP_201_CREATED)
async def create_payroll_run(
    payload: PayrollRunCreate,
    user: CurrentUser = Depends(require_role("hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.create_or_recalculate_run(session, user.id, payload.month)


@router.get("/runs", response_model=PayrollRunListResponse)
async def get_payroll_runs(
    _: CurrentUser = Depends(require_role("admin", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.list_runs(session)


@router.get("/runs/{run_id}", response_model=PayrollRunResponse)
async def get_payroll_run(
    run_id: UUID,
    _: CurrentUser = Depends(require_role("admin", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.get_run(session, run_id)


@router.post("/runs/{run_id}/finalize", response_model=PayrollRunResponse)
async def finalize_payroll_run(
    run_id: UUID,
    user: CurrentUser = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.finalize_payroll_run(session, user.id, run_id)


@router.get("/payslips", response_model=PayslipListResponse)
async def get_payslips(
    month: date | None = Query(default=None),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if user.role == "employee":
        if user.employee_id is None:
            raise AppError(403, "employee_profile_missing", "No employee record is linked to this account.")
        employee_id = user.employee_id
    elif user.role in {"admin", "hr"}:
        employee_id = None
    else:
        raise AppError(403, "forbidden", "You do not have permission to access payslips.")
    return await service.list_payslips(session, month, employee_id)


@payslip_pdf_router.get("/{payslip_id}/pdf")
async def download_payslip_pdf(
    payslip_id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    payslip = await service.get_payslip(session, payslip_id)
    if user.role == "employee" and user.employee_id != payslip["employee_id"]:
        raise AppError(403, "forbidden", "You cannot access another employee's payslip.")
    if user.role not in {"admin", "hr", "employee"}:
        raise AppError(403, "forbidden", "You do not have permission to access payslips.")
    employee = payslip["employee"]
    pdf_bytes = build_payslip_pdf_bytes(
        company_name=payslip["company_name"],
        employee={
            "full_name": employee["full_name"],
            "employee_code": employee["code"],
            "department": employee["department"] or "N/A",
            "designation": employee["designation"] or "N/A",
            "basic_salary": payslip["basic"],
        },
        payslip={
            "basic_salary": payslip["basic"],
            "gross": payslip["gross"],
            "deduction": payslip["deduction"],
            "tax": payslip["tax"],
            "net": payslip["net"],
        },
        month=payslip["month"].strftime("%B %Y"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip_{payslip_id}.pdf"},
    )
