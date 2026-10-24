from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

# Bounded, read-only AI tools enforcing scope and permissions per PROJECT.md & ABDULLAH.md.
# Employees may only access their own attendance/balance/leave. Colleague data or salary queries are refused.

async def tool_get_headcount(session: AsyncSession, user: Any, department_id: Optional[str] = None) -> Dict[str, Any]:
    """Get active headcount."""
    if user.role == "employee":
        return {"error": "Permission denied: employees cannot view headcount statistics."}
    # Import dashboard service or repo function when available; stub fallback if needed
    try:
        from app.modules.dashboards.service import get_headcount_service
        count = await get_headcount_service(session, user, department_id)
        return {"headcount": count}
    except Exception as e:
        return {"headcount": 0, "note": f"Service unavailable: {str(e)}"}

async def tool_get_attendance_summary(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """Get attendance summary."""
    if user.role == "employee":
        # Force scoped employee id for employee
        return {"message": "Attendance summary for your scoped view.", "employee_id": user.employee_id}
    try:
        from app.modules.dashboards.service import get_attendance_summary_service
        res = await get_attendance_summary_service(session, user, from_date, to_date, department_id)
        return res
    except Exception as e:
        return {"attendance_summary": [], "error": str(e)}

async def tool_get_late_comers(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """Get top late comers."""
    if user.role == "employee":
        return {"error": "Permission denied: employees cannot view late comers list."}
    try:
        from app.modules.dashboards.service import get_late_comers_service
        res = await get_late_comers_service(session, user, from_date, to_date, department_id, limit)
        return {"top_late": res}
    except Exception as e:
        return {"top_late": [], "error": str(e)}

async def tool_get_leave_summary(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """Get leave summary."""
    if user.role == "employee":
        return {"error": "Permission denied: employees cannot view company leave summaries."}
    try:
        from app.modules.dashboards.service import get_leave_summary_service
        res = await get_leave_summary_service(session, user, from_date, to_date, department_id)
        return {"leave_summary": res}
    except Exception as e:
        return {"leave_summary": [], "error": str(e)}

async def tool_get_my_leave_balance(session: AsyncSession, user: Any) -> Dict[str, Any]:
    """Get current user's leave balance."""
    if not user.employee_id:
        return {"error": "No employee profile linked to current user."}
    try:
        from app.modules.leave.service import get_leave_balance_service
        res = await get_leave_balance_service(session, user.employee_id)
        return {"leave_balance": res}
    except Exception as e:
        return {"leave_balance": [], "error": str(e)}

async def tool_get_payroll_summary(session: AsyncSession, user: Any, month: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """Get payroll summary. Employees are strictly refused salary/payroll data."""
    if user.role == "employee":
        return {"error": "Access denied: employees cannot view payroll summaries or salaries."}
    try:
        from app.modules.dashboards.service import get_payroll_summary_service
        res = await get_payroll_summary_service(session, user, month, department_id)
        return {"payroll_summary": res}
    except Exception as e:
        return {"payroll_summary": {}, "error": str(e)}

async def tool_search_employees(session: AsyncSession, user: Any, query: str) -> Dict[str, Any]:
    """Search employees directory. Employees cannot view sensitive fields or salaries."""
    if user.role == "employee":
        return {"error": "Permission denied: employee directory search is restricted to HR and Admin."}
    try:
        from app.modules.employees.service import search_employees_service
        res = await search_employees_service(session, query)
        return {"employees": res}
    except Exception as e:
        return {"employees": [], "error": str(e)}

# Tool dispatcher mapping
AI_TOOLS_MAP = {
    "get_headcount": tool_get_headcount,
    "get_attendance_summary": tool_get_attendance_summary,
    "get_late_comers": tool_get_late_comers,
    "get_leave_summary": tool_get_leave_summary,
    "get_my_leave_balance": tool_get_my_leave_balance,
    "get_payroll_summary": tool_get_payroll_summary,
    "search_employees": tool_search_employees,
}

AI_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_headcount",
            "description": "Get total active headcount in the company or department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"type": "string", "description": "Optional department ID filter"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_summary",
            "description": "Get attendance summary metrics between dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "department_id": {"type": "string", "description": "Optional department ID"}
                },
                "required": ["from_date", "to_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_late_comers",
            "description": "Get top late-coming employees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "department_id": {"type": "string", "description": "Optional department"},
                    "limit": {"type": "integer", "description": "Max results, default 5"}
                },
                "required": ["from_date", "to_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_summary",
            "description": "Get leave utilization summary by type and department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "department_id": {"type": "string", "description": "Optional department"}
                },
                "required": ["from_date", "to_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_leave_balance",
            "description": "Get remaining leave balances for the currently logged-in employee.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_payroll_summary",
            "description": "Get monthly payroll cost and summary. Admin/HR only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Month YYYY-MM-DD or YYYY-MM"},
                    "department_id": {"type": "string", "description": "Optional department"}
                },
                "required": ["month"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_employees",
            "description": "Search employees by name or code. Admin/HR only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]
