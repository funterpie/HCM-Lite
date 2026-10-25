"""SQL aggregation queries used by the HR dashboard."""

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_headcount(
    session: AsyncSession,
    from_: date,
    to: date,
    department_id: str | None = None,
) -> dict[str, int]:
    result = await session.execute(
        text(
            "SELECT count(*) AS headcount FROM employees "
            "WHERE join_date <= :to_date "
            "AND (exit_date IS NULL OR exit_date >= :to_date) "
            "AND status IN ('active', 'probation') "
            "AND (:department_id IS NULL OR department_id = CAST(:department_id AS uuid))"
        ),
        {"to_date": to, "department_id": department_id},
    )
    return {"headcount": int(result.scalar_one())}


async def get_attendance_trend(
    session: AsyncSession,
    from_: date,
    to: date,
    department_id: str | None = None,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT day AS date, "
            "round(100.0 * (count(*) FILTER (WHERE status IN "
            "('present', 'late', 'missing_checkout')) + "
            "0.5 * count(*) FILTER (WHERE status = 'half_day')) / "
            "NULLIF(count(*) FILTER (WHERE status <> 'on_leave'), 0), 2) AS rate "
            "FROM v_daily_status "
            "WHERE day BETWEEN :from_date AND :to_date "
            "AND (:department_id IS NULL OR department_id = CAST(:department_id AS uuid)) "
            "GROUP BY day ORDER BY day"
        ),
        {"from_date": from_, "to_date": to, "department_id": department_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_absenteeism_by_dept(
    session: AsyncSession,
    from_: date,
    to: date,
    department_id: str | None = None,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT d.id AS department_id, d.name AS department, "
            "round(100.0 * count(*) FILTER (WHERE v.status = 'absent') / "
            "NULLIF(count(*) FILTER (WHERE v.status <> 'on_leave'), 0), 2) AS pct "
            "FROM v_daily_status AS v "
            "JOIN departments AS d ON d.id = v.department_id "
            "WHERE v.day BETWEEN :from_date AND :to_date "
            "AND (:department_id IS NULL OR v.department_id = CAST(:department_id AS uuid)) "
            "GROUP BY d.id, d.name ORDER BY d.name"
        ),
        {"from_date": from_, "to_date": to, "department_id": department_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_leave_by_type(
    session: AsyncSession,
    from_: date,
    to: date,
    department_id: str | None = None,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "WITH approved_leave_days AS ("
            "SELECT lr.leave_type_id, count(*)::integer AS days "
            "FROM leave_requests AS lr "
            "JOIN employees AS e ON e.id = lr.employee_id "
            "CROSS JOIN settings AS s "
            "CROSS JOIN LATERAL generate_series("
            "GREATEST(lr.start_date, :from_date)::timestamp, "
            "LEAST(lr.end_date, :to_date)::timestamp, INTERVAL '1 day') "
            "AS generated(day) "
            "WHERE lr.status = 'approved' AND lr.start_date <= :to_date "
            "AND lr.end_date >= :from_date AND s.id = 1 "
            "AND NOT (EXTRACT(ISODOW FROM generated.day)::integer = ANY(s.weekend_days)) "
            "AND NOT EXISTS (SELECT 1 FROM holidays AS h WHERE h.date = generated.day::date) "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid)) "
            "GROUP BY lr.leave_type_id) "
            "SELECT lt.id AS leave_type_id, lt.name AS type, "
            "COALESCE(ald.days, 0)::integer AS days "
            "FROM leave_types AS lt LEFT JOIN approved_leave_days AS ald "
            "ON ald.leave_type_id = lt.id ORDER BY lt.name"
        ),
        {"from_date": from_, "to_date": to, "department_id": department_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_late_comers(
    session: AsyncSession,
    limit: int = 5,
    from_: date | None = None,
    to: date | None = None,
    department_id: str | None = None,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT e.id AS employee_id, e.full_name AS employee, "
            "count(*)::integer AS count, max(a.check_in) AS last_check_in "
            "FROM attendance AS a JOIN employees AS e ON e.id = a.employee_id "
            "WHERE a.date BETWEEN COALESCE(:from_date, date_trunc('month', "
            "clock_timestamp() AT TIME ZONE (SELECT timezone FROM settings WHERE id = 1))::date) "
            "AND COALESCE(:to_date, (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date) "
            "AND a.status = 'late' "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid)) "
            "GROUP BY e.id, e.full_name ORDER BY count DESC, e.full_name LIMIT :limit"
        ),
        {
            "from_date": from_,
            "to_date": to,
            "department_id": department_id,
            "limit": limit,
        },
    )
    return [dict(row) for row in result.mappings().all()]


async def get_pending_approvals(
    session: AsyncSession,
    from_: date | None = None,
    to: date | None = None,
    department_id: str | None = None,
) -> dict[str, int]:
    result = await session.execute(
        text(
            "SELECT ("
            "SELECT count(*) FROM leave_requests AS lr "
            "JOIN employees AS e ON e.id = lr.employee_id "
            "WHERE lr.status = 'pending' "
            "AND (:from_date IS NULL OR lr.start_date >= :from_date) "
            "AND (:to_date IS NULL OR lr.start_date <= :to_date) "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
            ") + ("
            "SELECT count(*) FROM attendance_corrections AS ac "
            "JOIN employees AS e ON e.id = ac.employee_id "
            "WHERE ac.status = 'pending' "
            "AND (:from_date IS NULL OR ac.date >= :from_date) "
            "AND (:to_date IS NULL OR ac.date <= :to_date) "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
            ") AS pending_approvals"
        ),
        {"from_date": from_, "to_date": to, "department_id": department_id},
    )
    return dict(result.mappings().one())


async def get_present_today(
    session: AsyncSession,
    department_id: str | None = None,
) -> dict[str, int]:
    result = await session.execute(
        text(
            "SELECT (SELECT count(*)::integer FROM attendance AS a "
            "JOIN employees AS e ON e.id = a.employee_id "
            "WHERE a.date = (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date "
            "AND a.status IN ('present', 'late', 'half_day', 'missing_checkout') "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
            ") AS present, (SELECT count(DISTINCT lr.employee_id)::integer "
            "FROM leave_requests AS lr JOIN employees AS e ON e.id = lr.employee_id "
            "WHERE lr.status = 'approved' AND lr.start_date <= (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date "
            "AND lr.end_date >= (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
            ") AS on_leave, (SELECT count(*)::integer FROM attendance AS a "
            "JOIN employees AS e ON e.id = a.employee_id "
            "WHERE a.date = (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date AND a.status = 'late' "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
            ") AS late_today"
        ),
        {"department_id": department_id},
    )
    return dict(result.mappings().one())


async def get_attrition(session: AsyncSession, from_: date, to: date) -> dict[str, Any]:
    result = await session.execute(
        text(
            "WITH counts AS ("
            "SELECT count(*) FILTER (WHERE exit_date BETWEEN :from_date AND :to_date) AS exits, "
            "count(*) FILTER (WHERE join_date <= :from_date AND "
            "(exit_date IS NULL OR exit_date >= :from_date)) AS start_count, "
            "count(*) FILTER (WHERE join_date <= :to_date AND "
            "(exit_date IS NULL OR exit_date >= :to_date)) AS end_count "
            "FROM employees) SELECT exits::integer AS exits, "
            "round(100.0 * exits / NULLIF((start_count + end_count) / 2.0, 0), 2) AS pct "
            "FROM counts"
        ),
        {"from_date": from_, "to_date": to},
    )
    return dict(result.mappings().one())


async def get_payroll_cost(
    session: AsyncSession, month: date, department_id: str | None = None
) -> dict[str, Any]:
    result = await session.execute(
        text(
            "SELECT COALESCE(sum(p.gross), 0) AS gross, COALESCE(sum(p.net), 0) AS net "
            "FROM payslips AS p JOIN payroll_runs AS r ON r.id = p.run_id "
            "JOIN employees AS e ON e.id = p.employee_id "
            "WHERE r.month = :month "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
        ),
        {"month": month, "department_id": department_id},
    )
    return dict(result.mappings().one())


async def get_avg_salary_by_dept_designation(
    session: AsyncSession,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT d.id AS department_id, d.name AS department, "
            "g.id AS designation_id, g.name AS designation, "
            "round(avg(e.basic_salary * 1.5), 2) AS average_gross_salary "
            "FROM employees AS e LEFT JOIN departments AS d ON d.id = e.department_id "
            "LEFT JOIN designations AS g ON g.id = e.designation_id "
            "WHERE e.status IN ('active', 'probation') "
            "GROUP BY d.id, d.name, g.id, g.name ORDER BY d.name, g.name"
        )
    )
    return [dict(row) for row in result.mappings().all()]


async def get_headcount_by_dept(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT d.id AS department_id, d.name AS department, "
            "count(e.id)::integer AS headcount "
            "FROM departments AS d LEFT JOIN employees AS e ON e.department_id = d.id "
            "AND e.status IN ('active', 'probation') "
            "AND e.join_date <= (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date "
            "AND (e.exit_date IS NULL OR e.exit_date >= (clock_timestamp() AT TIME ZONE "
            "(SELECT timezone FROM settings WHERE id = 1))::date) "
            "GROUP BY d.id, d.name ORDER BY d.name"
        )
    )
    return [dict(row) for row in result.mappings().all()]


async def get_payroll_cost_by_dept(session: AsyncSession, month: date) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT d.id AS department_id, d.name AS department, "
            "COALESCE(sum(p.gross), 0) AS gross, COALESCE(sum(p.net), 0) AS net "
            "FROM departments AS d LEFT JOIN employees AS e ON e.department_id = d.id "
            "LEFT JOIN (SELECT p.employee_id, p.gross, p.net FROM payslips AS p "
            "JOIN payroll_runs AS r ON r.id = p.run_id WHERE r.month = :month) AS p "
            "ON p.employee_id = e.id "
            "GROUP BY d.id, d.name ORDER BY d.name"
        ),
        {"month": month},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_gender_split(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT COALESCE(NULLIF(trim(gender), ''), 'unspecified') AS gender, "
            "count(*)::integer AS count FROM employees "
            "WHERE status IN ('active', 'probation') GROUP BY 1 ORDER BY 1"
        )
    )
    return [dict(row) for row in result.mappings().all()]


async def get_tenure_buckets(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT CASE WHEN age(current_date, join_date) < interval '1 year' THEN '<1 year' "
            "WHEN age(current_date, join_date) < interval '3 years' THEN '1-3 years' "
            "WHEN age(current_date, join_date) < interval '5 years' THEN '3-5 years' "
            "ELSE '5+ years' END AS tenure, count(*)::integer AS count "
            "FROM employees WHERE status IN ('active', 'probation') "
            "GROUP BY 1 ORDER BY min(join_date)"
        )
    )
    return [dict(row) for row in result.mappings().all()]


async def get_audit_feed(session: AsyncSession, limit: int = 10) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT a.id, a.actor_id, u.email AS actor_email, a.action, a.entity, "
            "a.entity_id, a.created_at FROM audit_logs AS a "
            "LEFT JOIN auth.users AS u ON u.id = a.actor_id "
            "ORDER BY a.created_at DESC, a.id DESC LIMIT :limit"
        ),
        {"limit": limit},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_hours_this_week(session: AsyncSession, employee_id: str) -> dict[str, Any]:
    result = await session.execute(
        text(
            "SELECT COALESCE(round(sum(extract(epoch FROM (a.check_out - a.check_in)) / 3600)::numeric, 2), 0) "
            "AS hours FROM attendance AS a CROSS JOIN settings AS s "
            "WHERE a.employee_id = CAST(:employee_id AS uuid) AND s.id = 1 "
            "AND a.check_in IS NOT NULL AND a.check_out IS NOT NULL "
            "AND (a.check_in AT TIME ZONE s.timezone)::date >= date_trunc('week', "
            "(clock_timestamp() AT TIME ZONE s.timezone))::date "
            "AND (a.check_in AT TIME ZONE s.timezone)::date <= "
            "(clock_timestamp() AT TIME ZONE s.timezone)::date"
        ),
        {"employee_id": employee_id},
    )
    return dict(result.mappings().one())


async def get_late_count(
    session: AsyncSession, employee_id: str, from_: date, to: date
) -> dict[str, int]:
    result = await session.execute(
        text(
            "SELECT count(*)::integer AS late_count FROM attendance "
            "WHERE employee_id = CAST(:employee_id AS uuid) "
            "AND date BETWEEN :from_date AND :to_date AND status = 'late'"
        ),
        {"employee_id": employee_id, "from_date": from_, "to_date": to},
    )
    return dict(result.mappings().one())


async def get_last_payslip(session: AsyncSession, employee_id: str) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            "SELECT p.*, r.month FROM payslips AS p "
            "JOIN payroll_runs AS r ON r.id = p.run_id "
            "WHERE p.employee_id = CAST(:employee_id AS uuid) "
            "ORDER BY r.month DESC LIMIT 1"
        ),
        {"employee_id": employee_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None
