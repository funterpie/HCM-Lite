# SAQIB: Backend (rules engine, attendance, leave, payroll maths)

Read `PROJECT.md` first. Everything there is binding. This file is your task list.

## You own (only you edit these)
- `backend/app/rules/*` (pure functions, the single source of truth for status and money)
- `modules/attendance`, `modules/leave`
- `backend/tests/*`
- The payroll **calculation** (`rules/payroll.py`). Taha owns the payroll endpoints and calls your function.

## Step 1 (first 30 min, others depend on you): `rules/` with tests
Implement the signatures in PROJECT.md section 10, with no database access:
- `working_days(start, end, holidays, weekend)`
- `attendance_status(check_in, check_out, settings)`: late after start+grace, half_day under 5 h, missing_checkout when the day is over
- `daily_status(...)`: present, late, half_day, missing_checkout, absent, on_leave, or `None` for non-working days. **Used by dashboards, payroll and AI**, so correctness here matters most.
- `compute_tax_monthly(gross)`: the slab table in PROJECT.md section 7
- `compute_payslip(...)`: gross 1.5 x basic, per day, deductions, proration for joiners/leavers, net
- `leave_balance`, `haversine_m`
- Use `Decimal` for money, and `settings.timezone` for time-of-day.

Push with pytest cases (about 15): on-time, late, exactly at 09:15 (not late), half day, weekend and holiday skipping, joiner mid-month, each tax slab boundary (600k, 1.2M, 2.4M, 3.6M), unpaid leave deduction, leave over balance.

## Task checklist
- [ ] Rules + tests pushed (T+0:30)
- [ ] `POST /attendance/check-in`: server time, one per day (409 `already_checked_in`), status via rules, source `web`
- [ ] `POST /attendance/check-out`: updates hours, applies half_day rule, 409/422 if no check-in
- [ ] `GET /attendance` calendar (Employee forced to own via `scoped_employee_id`), merging stored rows with computed absent/on_leave days
- [ ] `GET /attendance/board?date&department_id` for HR/Admin
- [ ] Corrections: request (Employee), list, approve/reject (HR), upsert row with `source='correction'`, notify, audit
- [ ] Leave: apply (working days only, **422 on overlap or over-balance**, error codes `overlap` / `insufficient_balance`), cancel, list, balance (computed), decide (HR, comment required on reject), notify, audit
- [ ] Payroll input helper: for each employee and month, return the list of daily statuses and unpaid leave days for Taha's endpoint
- [ ] Bonus if time: late penalty (3 lates = 0.5 day) behind `settings.late_penalty_enabled`

## Rules you must not break
- Never trust client time. Never store absent or missing_checkout. Compute them.
- Dashboards (Abdullah) and AI tools call **your** services, so expose clean functions like `get_attendance_summary(session, user, from, to, department_id)` and `get_leave_summary(...)`, not just routes.
- Use `audit.log` from `core/audit.py` (Taha) on approve/reject/correct.

## First prompt to paste into your AI coding tool
```
Read PROJECT.md and SAQIB.md. In backend/app/rules/ implement the pure functions from PROJECT.md section 10
(working_days, attendance_status, daily_status, compute_tax_monthly, compute_payslip, leave_balance, haversine_m)
using Decimal for money and the exact rules from section 7. No DB access in rules/.
Then write backend/tests/ with pytest covering: on-time vs late (09:15 boundary is NOT late), half_day under 5h,
weekend/holiday skipping, joiner mid-month proration, every tax slab boundary (600k, 1.2M, 2.4M, 3.6M),
unpaid leave deduction, leave over-balance. Run the tests and show me the output.
```

## Definition of done
- All tests pass.
- Check in twice returns 409. Leave overlap returns 422. Balance after approval is correct.
- Dashboard attendance rate (Abdullah) and the board agree because both use `daily_status`.
