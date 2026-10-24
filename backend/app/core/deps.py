from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

from app.db import get_db
from app.core.security import security, verify_jwt

class CurrentUser:
    def __init__(self, id: str, email: str, role: str, employee_id: Optional[str], must_change_password: bool, is_active: bool):
        self.id = id
        self.email = email
        self.role = role
        self.employee_id = employee_id
        self.must_change_password = must_change_password
        self.is_active = is_active

async def current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: AsyncSession = Depends(get_db)) -> CurrentUser:
    payload = verify_jwt(credentials)
    user_id = payload.get("sub") or payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject.")

    # Load profile from profiles table (never trust role from token)
    query = text("SELECT id, email, role, employee_id, must_change_password, is_active FROM profiles WHERE id = :uid")
    res = await session.execute(query, {"uid": user_id})
    row = res.fetchone()

    if not row:
        # Fallback for first-run or missing profile
        return CurrentUser(id=user_id, email=payload.get("email", ""), role="admin", employee_id=None, must_change_password=False, is_active=True)

    if not row.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated.")

    return CurrentUser(
        id=str(row.id),
        email=row.email,
        role=row.role,
        employee_id=str(row.employee_id) if row.employee_id else None,
        must_change_password=row.must_change_password,
        is_active=row.is_active
    )

def require_role(*roles: str):
    def dependency(user: CurrentUser = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role '{user.role}' is not authorized for this action.")
        return user
    return dependency

def scoped_employee_id(user: CurrentUser = Depends(current_user)) -> Optional[str]:
    """Returns own employee_id for employee role, None (all) for admin/hr."""
    if user.role == "employee":
        if not user.employee_id:
            raise HTTPException(status_code=403, detail="Employee profile not linked.")
        return user.employee_id
    return None
