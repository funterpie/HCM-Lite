from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, current_user, require_role
from app.core.errors import AppError
from app.db import get_session
from app.modules.employees import service
from app.modules.employees.schemas import (
    EmployeeCreate,
    EmployeePage,
    EmployeeResponse,
    EmployeeUpdate,
    ProfileUpdate,
    SalaryUpdate,
)

router = APIRouter(tags=["employees"])


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("hr"))],
) -> EmployeeResponse:
    data = payload.model_dump(exclude={"temp_password"})
    result = await service.create_employee(
        session, user.id, data, payload.temp_password.get_secret_value()
    )
    return EmployeeResponse(data=result)


@router.get("/employees", response_model=EmployeePage)
async def list_employees(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(require_role("admin", "hr"))],
    q: str | None = None,
    department_id: UUID | None = None,
    employee_status: str | None = Query(default=None, alias="status", pattern="^(active|probation|exited)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> EmployeePage:
    rows, total = await service.list_employees(
        session, q, department_id, employee_status, page, page_size
    )
    return EmployeePage(
        data=rows,
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("admin", "hr", "employee"))],
) -> EmployeeResponse:
    if user.role == "employee" and user.employee_id != employee_id:
        raise AppError(403, "forbidden", "You may only view your own employee record.")
    return EmployeeResponse(data=await service.get_employee(session, employee_id))


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("hr"))],
) -> EmployeeResponse:
    result = await service.update_employee(
        session, user.id, employee_id, payload.model_dump()
    )
    return EmployeeResponse(data=result)


@router.patch("/me/profile", response_model=EmployeeResponse)
async def update_my_profile(
    payload: ProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(current_user)],
) -> EmployeeResponse:
    return EmployeeResponse(
        data=await service.update_my_profile(
            session, user.id, payload.model_dump(exclude_unset=True)
        )
    )


@router.put("/employees/{employee_id}/salary", response_model=EmployeeResponse)
async def update_salary(
    employee_id: UUID,
    payload: SalaryUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("hr"))],
) -> EmployeeResponse:
    result = await service.update_salary(
        session, user.id, employee_id, payload.basic_salary
    )
    return EmployeeResponse(data=result)
