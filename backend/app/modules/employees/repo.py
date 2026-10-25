from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_EMPLOYEE_COLUMNS = (
    "e.id, e.user_id, e.code, e.email, e.full_name, e.phone, e.address, e.gender, "
    "e.department_id, d.name AS department, e.designation_id, g.name AS designation, "
    "e.join_date, e.exit_date, e.status, e.basic_salary, p.role, p.is_active, "
    "p.must_change_password"
)
_EMPLOYEE_FROM = (
    "FROM employees e LEFT JOIN departments d ON d.id = e.department_id "
    "LEFT JOIN designations g ON g.id = e.designation_id "
    "LEFT JOIN profiles p ON p.id = e.user_id"
)


async def department_exists(session: AsyncSession, department_id: UUID) -> bool:
    result = await session.execute(text("SELECT EXISTS (SELECT 1 FROM departments WHERE id = :id)"), {"id": department_id})
    return bool(result.scalar_one())


async def designation_exists(session: AsyncSession, designation_id: UUID) -> bool:
    result = await session.execute(text("SELECT EXISTS (SELECT 1 FROM designations WHERE id = :id)"), {"id": designation_id})
    return bool(result.scalar_one())


async def create_profile(session: AsyncSession, user_id: UUID, role: str) -> None:
    await session.execute(
        text(
            "INSERT INTO profiles (id, role, must_change_password, is_active) "
            "VALUES (:id, :role, true, true)"
        ),
        {"id": user_id, "role": role},
    )


async def create_employee(session: AsyncSession, user_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
    result = await session.execute(
        text(
            "INSERT INTO employees (user_id, code, email, full_name, phone, address, gender, "
            "department_id, designation_id, join_date, status, basic_salary) "
            "VALUES (:user_id, :code, :email, :full_name, :phone, :address, :gender, "
            ":department_id, :designation_id, :join_date, :status, :basic_salary) "
            "RETURNING id, user_id, code, email, full_name, phone, address, gender, "
            "department_id, designation_id, join_date, exit_date, status, basic_salary"
        ),
        {**data, "user_id": user_id},
    )
    return dict(result.mappings().one())


async def get_employee(session: AsyncSession, employee_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text(f"SELECT {_EMPLOYEE_COLUMNS} {_EMPLOYEE_FROM} WHERE e.id = :id"),
        {"id": employee_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def get_employee_by_user(session: AsyncSession, user_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text(f"SELECT {_EMPLOYEE_COLUMNS} {_EMPLOYEE_FROM} WHERE e.user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def list_employees(
    session: AsyncSession,
    query: str | None,
    department_id: UUID | None,
    employee_status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = []
    params: dict[str, Any] = {
        "query": f"%{query.strip()}%" if query and query.strip() else None,
        "department_id": department_id,
        "status": employee_status,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    if params["query"] is not None:
        where.append("(e.full_name ILIKE :query OR e.code ILIKE :query OR e.email ILIKE :query)")
    if department_id is not None:
        where.append("e.department_id = :department_id")
    if employee_status is not None:
        where.append("e.status = :status")
    condition = " WHERE " + " AND ".join(where) if where else ""
    total_result = await session.execute(
        text(f"SELECT count(*) {_EMPLOYEE_FROM}{condition}"), params
    )
    total = int(total_result.scalar_one())
    result = await session.execute(
        text(
            f"SELECT {_EMPLOYEE_COLUMNS} {_EMPLOYEE_FROM}{condition} "
            "ORDER BY e.full_name, e.id LIMIT :limit OFFSET :offset"
        ),
        params,
    )
    return [dict(row) for row in result.mappings().all()], total


async def update_employee(
    session: AsyncSession, employee_id: UUID, values: dict[str, Any]
) -> dict[str, Any] | None:
    assignments = ", ".join(f"{column} = :{column}" for column in values)
    result = await session.execute(
        text(
            f"UPDATE employees SET {assignments} WHERE id = :employee_id "
            "RETURNING id, user_id, code, email, full_name, phone, address, gender, "
            "department_id, designation_id, join_date, exit_date, status, basic_salary"
        ),
        {**values, "employee_id": employee_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def update_profile_fields(
    session: AsyncSession, user_id: UUID, values: dict[str, Any]
) -> dict[str, Any] | None:
    assignments = ", ".join(f"{column} = :{column}" for column in values)
    result = await session.execute(
        text(
            f"UPDATE employees SET {assignments} WHERE user_id = :user_id "
            "RETURNING id, user_id, phone, address"
        ),
        {**values, "user_id": user_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def set_salary(
    session: AsyncSession, employee_id: UUID, basic_salary: Any
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            "UPDATE employees SET basic_salary = :basic_salary WHERE id = :employee_id "
            "RETURNING id, basic_salary"
        ),
        {"employee_id": employee_id, "basic_salary": basic_salary},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def employee_360_last_payslip(session: AsyncSession, employee_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            "SELECT p.id, r.month, p.basic, p.gross, p.working_days, p.absent_days, "
            "p.unpaid_days, p.half_days, p.deduction, p.tax, p.net "
            "FROM payslips p JOIN payroll_runs r ON r.id = p.run_id "
            "WHERE p.employee_id = :employee_id ORDER BY r.month DESC LIMIT 1"
        ),
        {"employee_id": employee_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None
