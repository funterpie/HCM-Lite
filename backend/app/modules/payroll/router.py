from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db import get_session
from app.core.deps import current_user
from app.modules.payroll.pdf import build_payslip_pdf_bytes

router = APIRouter(prefix="/payslips", tags=["payroll"])

@router.get("/{id}/pdf")
async def download_payslip_pdf(
    id: str,
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(current_user)
):
    """Download payslip PDF (scoped: Employee own payslip, Admin/HR all)."""
    # Fetch payslip and employee details
    from sqlalchemy import text
    res = await session.execute(text("""
        pr.id, pr.gross, pr.deduction, pr.tax, pr.net, pr.month,
        e.id as employee_id, e.full_name, e.employee_code, d.name as department, des.title as designation, e.basic_salary
        FROM payslips pr
        JOIN employees e ON e.id = pr.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        LEFT JOIN designations des ON des.id = e.designation_id
        WHERE pr.id = CAST(:pid AS uuid)
    """), {"pid": id})
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Payslip not found.")

    # Scope check: employee can only download own payslip
    if user.role == "employee":
        if str(row.employee_id) != str(user.employee_id):
            raise HTTPException(status_code=403, detail="Access denied to other employee's payslip.")

    employee_info = {
        "full_name": row.full_name,
        "employee_code": row.employee_code,
        "department": row.department or "N/A",
        "designation": row.designation or "N/A",
        "basic_salary": float(row.basic_salary or 0)
    }
    payslip_data = {
        "basic_salary": float(row.basic_salary or 0),
        "gross": float(row.gross or 0),
        "deduction": float(row.deduction or 0),
        "tax": float(row.tax or 0),
        "net": float(row.net or 0)
    }

    pdf_bytes = await build_payslip_pdf_bytes(
        company_name="HCM Lite Company",
        employee=employee_info,
        payslip=payslip_data,
        month=str(row.month)
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip_{id}.pdf"}
    )
