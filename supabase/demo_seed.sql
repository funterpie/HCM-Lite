BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM settings WHERE id = 1) THEN
        RAISE EXCEPTION 'Complete /setup before loading demo data';
    END IF;
END $$;

INSERT INTO departments (name)
VALUES ('Engineering'), ('People Operations'), ('Customer Success')
ON CONFLICT (name) DO NOTHING;

INSERT INTO designations (name)
VALUES ('Software Engineer'), ('HR Manager'), ('Support Specialist')
ON CONFLICT (name) DO NOTHING;

INSERT INTO leave_types (name, yearly_quota, is_paid)
VALUES ('Annual', 14, true), ('Sick', 8, true), ('Casual', 10, true), ('Unpaid', NULL, false)
ON CONFLICT (name) DO NOTHING;

INSERT INTO holidays (date, name)
VALUES (make_date(EXTRACT(YEAR FROM CURRENT_DATE)::integer, 12, 25), 'Demo holiday')
ON CONFLICT (date) DO NOTHING;

INSERT INTO employees (
    code, email, full_name, phone, gender, department_id, designation_id,
    join_date, status, basic_salary
)
SELECT sample.code, sample.email, sample.full_name, sample.phone, sample.gender,
       department.id, designation.id, CURRENT_DATE - sample.days_employed,
       'active', sample.basic_salary
FROM (VALUES
    ('DEMO-001', 'alex.chen@example.com', 'Alex Chen', '+1-555-0101', 'male', 'Engineering', 'Software Engineer', 240, 180000::numeric),
    ('DEMO-002', 'samira.khan@example.com', 'Samira Khan', '+1-555-0102', 'female', 'People Operations', 'HR Manager', 390, 210000::numeric),
    ('DEMO-003', 'jordan.lee@example.com', 'Jordan Lee', '+1-555-0103', 'non-binary', 'Engineering', 'Software Engineer', 125, 165000::numeric),
    ('DEMO-004', 'maya.patel@example.com', 'Maya Patel', '+1-555-0104', 'female', 'Customer Success', 'Support Specialist', 75, 120000::numeric),
    ('DEMO-005', 'omar.hassan@example.com', 'Omar Hassan', '+1-555-0105', 'male', 'Engineering', 'Software Engineer', 30, 150000::numeric)
) AS sample(code, email, full_name, phone, gender, department, designation, days_employed, basic_salary)
JOIN departments AS department ON department.name = sample.department
JOIN designations AS designation ON designation.name = sample.designation
ON CONFLICT (code) DO NOTHING;

WITH workdays AS (
    SELECT generated.day::date AS day
    FROM settings AS s
    CROSS JOIN LATERAL generate_series(
        CURRENT_DATE - 30, CURRENT_DATE - 1, INTERVAL '1 day'
    ) AS generated(day)
    WHERE s.id = 1
      AND NOT (EXTRACT(ISODOW FROM generated.day)::integer = ANY(s.weekend_days))
      AND NOT EXISTS (SELECT 1 FROM holidays h WHERE h.date = generated.day::date)
), numbered AS (
    SELECT e.id AS employee_id, e.code, w.day,
           row_number() OVER (PARTITION BY e.id ORDER BY w.day) AS day_number
    FROM employees e CROSS JOIN workdays w
    WHERE e.code LIKE 'DEMO-%' AND e.join_date <= w.day
), attendance_rows AS (
    SELECT n.employee_id, n.day,
           CASE WHEN n.day_number % 11 = 0 THEN 'half_day'::att_status
                WHEN n.day_number % 5 = 0 THEN 'late'::att_status
                ELSE 'present'::att_status END AS status,
           CASE WHEN n.day_number % 11 = 0 THEN time '09:00'
                WHEN n.day_number % 5 = 0 THEN time '09:22'
                ELSE time '08:55' END AS local_check_in,
           CASE WHEN n.day_number % 11 = 0 THEN interval '4 hours'
                ELSE interval '8 hours' END AS work_duration
    FROM numbered n
    WHERE n.day_number % 7 <> 0
)
INSERT INTO attendance (employee_id, date, check_in, check_out, status, source)
SELECT r.employee_id, r.day,
       (r.day + r.local_check_in) AT TIME ZONE s.timezone,
       ((r.day + r.local_check_in) + r.work_duration) AT TIME ZONE s.timezone,
       r.status, 'web'
FROM attendance_rows r CROSS JOIN settings s
WHERE s.id = 1
ON CONFLICT (employee_id, date) DO NOTHING;

INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, days, reason, status)
SELECT e.id, lt.id, CURRENT_DATE - 12, CURRENT_DATE - 11, 2,
       'Demo approved annual leave', 'approved'
FROM employees e CROSS JOIN leave_types lt
WHERE e.code = 'DEMO-003' AND lt.name = 'Annual'
  AND NOT EXISTS (
      SELECT 1 FROM leave_requests lr
      WHERE lr.employee_id = e.id AND lr.reason = 'Demo approved annual leave'
  );

INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, days, reason, status)
SELECT e.id, lt.id, CURRENT_DATE + 7, CURRENT_DATE + 8, 2,
       'Demo leave awaiting review', 'pending'
FROM employees e CROSS JOIN leave_types lt
WHERE e.code = 'DEMO-005' AND lt.name = 'Casual'
  AND NOT EXISTS (
      SELECT 1 FROM leave_requests lr
      WHERE lr.employee_id = e.id AND lr.reason = 'Demo leave awaiting review'
  );

INSERT INTO announcements (title, body)
SELECT 'Welcome to the HCM Lite demo',
       'This sample announcement is for demonstration only.'
WHERE NOT EXISTS (
    SELECT 1 FROM announcements WHERE title = 'Welcome to the HCM Lite demo'
);

INSERT INTO payroll_runs (month, status)
VALUES (date_trunc('month', CURRENT_DATE - INTERVAL '1 month')::date, 'draft')
ON CONFLICT (month) DO NOTHING;

INSERT INTO payslips (
    run_id, employee_id, basic, gross, working_days, absent_days, unpaid_days,
    half_days, deduction, tax, net
)
SELECT r.id, e.id, e.basic_salary, e.basic_salary * 1.5, 22, 0, 0, 0,
       0,
       round(CASE
           WHEN e.basic_salary * 18 <= 600000 THEN 0
           WHEN e.basic_salary * 18 <= 1200000 THEN (e.basic_salary * 18 - 600000) * 0.05 / 12
           WHEN e.basic_salary * 18 <= 2400000 THEN (30000 + (e.basic_salary * 18 - 1200000) * 0.15) / 12
           WHEN e.basic_salary * 18 <= 3600000 THEN (210000 + (e.basic_salary * 18 - 2400000) * 0.25) / 12
           ELSE (510000 + (e.basic_salary * 18 - 3600000) * 0.35) / 12
       END, 2),
       e.basic_salary * 1.5 - round(CASE
           WHEN e.basic_salary * 18 <= 600000 THEN 0
           WHEN e.basic_salary * 18 <= 1200000 THEN (e.basic_salary * 18 - 600000) * 0.05 / 12
           WHEN e.basic_salary * 18 <= 2400000 THEN (30000 + (e.basic_salary * 18 - 1200000) * 0.15) / 12
           WHEN e.basic_salary * 18 <= 3600000 THEN (210000 + (e.basic_salary * 18 - 2400000) * 0.25) / 12
           ELSE (510000 + (e.basic_salary * 18 - 3600000) * 0.35) / 12
       END, 2)
FROM payroll_runs r
CROSS JOIN employees e
WHERE r.month = date_trunc('month', CURRENT_DATE - INTERVAL '1 month')::date
  AND e.code LIKE 'DEMO-%'
ON CONFLICT (run_id, employee_id) DO NOTHING;

COMMIT;
