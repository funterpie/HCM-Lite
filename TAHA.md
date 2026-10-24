# TAHA: Backend lead (core, auth, org setup, employees, comms)

Read `PROJECT.md` first. Everything there is binding. This file is your task list.

## You own (only you edit these)
- `backend/app/main.py`, `core/*`, `db.py`
- `modules/auth`, `modules/settings`, `modules/employees`, `modules/comms`
- `modules/payroll/router.py` (run endpoints, finalize). The maths comes from Saqib's `rules/`. PDF comes from Abdullah.
- Pydantic schemas = the API contract. Keep them accurate, since Farhan generates TypeScript types from `/openapi.json`.

## Everyone is blocked on you for the first 30 minutes, so move first
1. **T+0:00-0:15** Push the skeleton: FastAPI app, CORS from env, `GET /health`, `db.py` (async engine, `statement_cache_size=0`), `core/config.py`.
2. **T+0:15-0:30** Push `core/errors.py` (global handlers: output exactly `{error:{code,message,fields}}`, including for FastAPI validation errors and `HTTPException`), `core/security.py` (verify Supabase JWT), `core/deps.py` (`current_user`, `require_role`, `scoped_employee_id`), `core/audit.py::log(session, actor, action, entity, entity_id, before, after)`. Tell the team on chat when pushed.
3. Merge to `main` so Abdullah's Render deploy picks it up.

## Task checklist
- [ ] `POST /setup` (only while `settings` is empty), optional boot-time admin from `ADMIN_EMAIL`/`ADMIN_PASSWORD`
- [ ] `GET /me`, `POST /auth/change-password` (clears `must_change_password`), deactivated users get 403
- [ ] Settings GET/PUT, departments, designations, leave types (+ `/leave-types/defaults`), holidays (Admin write, HR read)
- [ ] `POST /users/hr`, `PATCH /users/{id}/active`, `POST /users/{id}/reset-password` (Supabase Admin API)
- [ ] Employees: create (creates Supabase user with temp password, profile, employee row, notification), update, list with `q`/`department_id`/`status`/paging, 360 view, `PATCH /me/profile` (phone, address only)
- [ ] `PUT /employees/{id}/salary` (HR only), audit before/after
- [ ] Payroll run endpoints: create/recompute draft (calls Saqib's `compute_payslip` for each active employee), list, get, finalize (Admin only, sets locked state, audit, notifies employees "payslip ready")
- [ ] Announcements (Admin/HR post), notifications (list, mark read), audit list (Admin only, filters)
- [ ] Employee CSV export; CSV import with `dry_run` (**only if time**; cut order is in PROJECT.md)
- [ ] Every create/update/approve/finalize calls `audit.log`

## Rules you must not break
- Role from `profiles`, never from the token. Employee reads are always filtered by `scoped_employee_id`.
- Temp password flow and first-run rules are in PROJECT.md section 6.
- Return the standard envelope everywhere. Never leak stack traces.
- HR cannot change settings, create Admins or finalize payroll. Admin cannot register employees (view only).

## First prompt to paste into your AI coding tool
```
Read PROJECT.md and TAHA.md in this repo. Build the FastAPI skeleton in backend/ exactly as in PROJECT.md section 3:
app/main.py, core/{config,security,deps,errors,audit}.py, db.py (SQLAlchemy 2 async, asyncpg, connect_args statement_cache_size=0).
Auth: verify the Supabase access token (JWKS if available, else HS256 with SUPABASE_JWT_SECRET), then load role/is_active/must_change_password from the profiles table.
Provide deps: current_user, require_role(*roles), scoped_employee_id(user).
Errors: global handlers returning {"error":{"code","message","fields"}} for HTTPException and RequestValidationError.
Add GET /health. Add requirements.txt and .env.example. Keep modules as router/service/repo/schemas. No business rules in routers.
```

## Definition of done
- Fresh Supabase + `POST /setup` yields a working Admin who can log in from the frontend.
- Registering an employee gives them a working login that must change its password.
- Payroll draft -> Admin finalize works, and editing after finalize fails.
- `/openapi.json` is accurate, so Farhan can generate types.
