import os
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.audit import log as audit_log

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

async def create_hr_user_service(session: AsyncSession, admin_user: any, payload: any) -> dict:
    """Create HR user via Supabase Admin API and employee profile record."""
    if admin_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can create HR logins.")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase admin configuration missing.")

    # 1. Create user in Supabase Auth Admin API
    admin_api_url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "email": payload.email,
        "password": payload.password,
        "email_confirm": True
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(admin_api_url, headers=headers, json=body)
        if resp.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"Supabase user creation failed: {resp.text}")
        user_data = resp.json()
        user_id = user_data.get("id")

    # 2. Insert profile & employee record using Taha's exposed function or safe insert
    try:
        from app.modules.employees.repo import create_employee_for_user_repo
        employee_id = await create_employee_for_user_repo(
            session,
            user_id=user_id,
            email=payload.email,
            full_name=payload.full_name,
            role="hr",
            department_id=payload.department_id,
            designation_id=payload.designation_id,
            basic_salary=payload.basic_salary
        )
    except Exception as e:
        # Fallback or propagate
        raise HTTPException(status_code=500, detail=f"Failed to create employee/profile record: {str(e)}")

    await audit_log(session, actor=admin_user.id, action="create_hr", entity="user", before=None, after={"email": payload.email, "user_id": user_id})
    return {"user_id": user_id, "employee_id": employee_id, "email": payload.email, "role": "hr"}

async def set_user_active_service(session: AsyncSession, admin_user: any, user_id: str, is_active: bool) -> dict:
    """Activate or deactivate any user login."""
    if admin_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")

    from sqlalchemy import text
    await session.execute(text("UPDATE profiles SET is_active = :active WHERE id = :uid"), {"active": is_active, "uid": user_id})
    await session.commit()
    await audit_log(session, actor=admin_user.id, action="set_active", entity="user", before=None, after={"user_id": user_id, "is_active": is_active})
    return {"user_id": user_id, "is_active": is_active}

async def reset_user_password_service(session: AsyncSession, admin_user: any, user_id: str, new_password: str) -> dict:
    """Reset user password via Supabase Admin API."""
    if admin_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")

    admin_api_url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.put(admin_api_url, headers=headers, json={"password": new_password})
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Password reset failed: {resp.text}")

    await audit_log(session, actor=admin_user.id, action="reset_password", entity="user", before=None, after={"user_id": user_id})
    return {"message": "Password reset successfully."}
