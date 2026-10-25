from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import verify_access_token
from app.db import get_session
from app.modules.auth import repo as auth_repo

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    role: str
    is_active: bool
    must_change_password: bool
    email: str | None = None
    employee_id: UUID | None = None


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "unauthorized", "A bearer access token is required.")

    claims = await verify_access_token(credentials.credentials)
    try:
        user_id = UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise AppError(401, "unauthorized", "The access token has no valid user ID.") from exc

    profile = await auth_repo.get_profile_for_user(session, user_id)
    if profile is None:
        raise AppError(401, "unauthorized", "The user profile was not found.")
    if not profile["is_active"]:
        raise AppError(403, "account_inactive", "This account is inactive.")

    employee_id = None
    if profile["role"] == "employee":
        employee_id = await auth_repo.get_employee_id_for_user(session, user_id)
        if employee_id is None:
            raise AppError(403, "employee_profile_missing", "No employee record is linked to this account.")

    return CurrentUser(
        id=user_id,
        role=profile["role"],
        is_active=profile["is_active"],
        must_change_password=profile["must_change_password"],
        email=claims.get("email"),
        employee_id=employee_id,
    )


def require_role(*roles: str):
    async def role_dependency(
        user: Annotated[CurrentUser, Depends(current_user)],
    ) -> CurrentUser:
        if user.role not in roles:
            raise AppError(403, "forbidden", "You do not have permission to perform this action.")
        return user

    return role_dependency


def scoped_employee_id(user: CurrentUser) -> UUID | None:
    if user.role == "employee":
        if user.employee_id is None:
            raise AppError(403, "employee_profile_missing", "No employee record is linked to this account.")
        return user.employee_id
    if user.role in {"admin", "hr"}:
        return None
    raise AppError(403, "forbidden", "You do not have permission to access employee data.")
