CREATE OR REPLACE VIEW v_daily_status AS
WITH company_clock AS (
    SELECT
        s.weekend_days,
        (clock_timestamp() AT TIME ZONE s.timezone)::date AS local_today
    FROM settings AS s
    WHERE s.id = 1
), employee_days AS (
    SELECT
        e.id AS employee_id,
        e.department_id,
        generated.day::date AS day
    FROM employees AS e
    CROSS JOIN company_clock AS c
    CROSS JOIN LATERAL generate_series(
        e.join_date::timestamp,
        LEAST(COALESCE(e.exit_date, c.local_today), c.local_today - 1)::timestamp,
        INTERVAL '1 day'
    ) AS generated(day)
    WHERE generated.day::date < c.local_today
      AND NOT (EXTRACT(ISODOW FROM generated.day)::integer = ANY(c.weekend_days))
      AND NOT EXISTS (
          SELECT 1 FROM holidays AS h WHERE h.date = generated.day::date
      )
)
SELECT
    d.employee_id,
    d.department_id,
    d.day,
    CASE
        WHEN lr.employee_id IS NOT NULL THEN 'on_leave'
        WHEN a.employee_id IS NOT NULL
             AND a.check_in IS NOT NULL
             AND a.check_out IS NULL
             AND d.day < c.local_today THEN 'missing_checkout'
        WHEN a.employee_id IS NOT NULL THEN a.status::text
        ELSE 'absent'
    END AS status
FROM employee_days AS d
CROSS JOIN company_clock AS c
LEFT JOIN attendance AS a
    ON a.employee_id = d.employee_id
   AND a.date = d.day
LEFT JOIN LATERAL (
    SELECT lr.employee_id
    FROM leave_requests AS lr
    WHERE lr.employee_id = d.employee_id
      AND lr.status = 'approved'
      AND lr.start_date <= d.day
      AND lr.end_date >= d.day
    LIMIT 1
) AS lr ON TRUE;
