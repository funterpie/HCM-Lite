from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class HRDashboardResponse(BaseModel):
    kpis: Dict[str, Any]
    attendance_trend: List[Dict[str, Any]]
    absenteeism_by_dept: List[Dict[str, Any]]
    leave_by_type: List[Dict[str, Any]]
    top_late: List[Dict[str, Any]]

class AdminDashboardResponse(BaseModel):
    kpis: Dict[str, Any]
    headcount_by_dept: List[Dict[str, Any]]
    payroll_cost_by_dept: List[Dict[str, Any]]
    gender_split: List[Dict[str, Any]]
    tenure_buckets: List[Dict[str, Any]]
    audit_feed: List[Dict[str, Any]]

class MeDashboardResponse(BaseModel):
    hours_this_week: float
    target_hours: float
    late_count: int
    leave_balance: List[Dict[str, Any]]
    last_payslip: Optional[Dict[str, Any]]
    announcements: List[Dict[str, Any]]
