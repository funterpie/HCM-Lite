# HCM Lite API Guide

This guide describes the API currently implemented on `main` and the workflow for adding more features. The API is a FastAPI service backed by Supabase Auth and PostgreSQL.

## Base URLs and documentation

- Local API base: `http://localhost:8000/api`
- Deployed API base: set this to the Render service URL followed by `/api`.
- Interactive OpenAPI docs: append `/docs` to the API host, for example `http://localhost:8000/docs`.
- Health check: `GET /health` or `GET /api/health` (no authentication).
- The server currently mounts routes both at the root and under `/api`; use `/api` for all new frontend and client integrations.

## Authentication and roles

Sign users in through Supabase Auth in the frontend. Send the returned access token to protected endpoints as `Authorization: Bearer <access-token>`. Do not send the Supabase service-role key to a browser or API client. The API verifies the access token, loads the application profile, checks that the user is active, and applies role checks.

| Role | Typical access |
| --- | --- |
| `admin` | Company configuration, user management, payroll finalization, audit, and admin dashboard |
| `hr` | Employee, attendance, leave, payroll, announcements, and HR dashboard operations |
| `employee` | Own profile, attendance, leave, notifications, and payslips |

Employee-scoped endpoints restrict employee data to the signed-in employee. A `403` means the account is authenticated but does not have the required permission; `401` means the token is missing or invalid.

First-time setup is a separate flow: check `GET /api/setup/status`, then, only when setup is needed, submit `POST /api/setup` to create the company and first admin. Setup is one-time. Normal sign-in is Supabase Auth, not an API login endpoint. Authenticated users can check their profile with `GET /api/me` and change their password with `POST /api/auth/change-password`.

## Endpoint index

All paths below are relative to the `/api` base. Unless marked **Public**, send a bearer access token. Request and response schemas are shown in the interactive `/docs` page.

| Area | Method and path | Access / purpose |
| --- | --- | --- |
| Health | `GET /health` | Public; service health |
| Setup | `GET /setup/status` | Public; whether initial setup is needed |
| Setup | `POST /setup` | Public, one-time; create company and first admin |
| Auth | `GET /me` | Any signed-in user; current profile and role |
| Auth | `POST /auth/change-password` | Any signed-in user; change password |
| Employees | `GET /employees` | Admin/HR; searchable, filtered, paginated directory |
| Employees | `POST /employees` | HR; create employee and login |
| Employees | `GET /employees/{employee_id}` | Admin/HR; employee details; employees can read their own |
| Employees | `PUT /employees/{employee_id}` | HR; update employee details |
| Employees | `PUT /employees/{employee_id}/salary` | HR; update salary |
| Employees | `PATCH /me/profile` | Any signed-in user; update own profile fields |
| Attendance | `POST /attendance/check-in` | Employee/HR; check in |
| Attendance | `POST /attendance/check-out` | Employee/HR; check out |
| Attendance | `GET /attendance?from=YYYY-MM-DD&to=YYYY-MM-DD` | Signed-in user; attendance calendar; optional `employee_id` |
| Attendance | `GET /attendance/board?date=YYYY-MM-DD` | Admin/HR; daily attendance board; optional `department_id` |
| Attendance | `POST /attendance/corrections` | Employee; request a correction |
| Attendance | `GET /attendance/corrections` | Employee/HR/Admin; list corrections; optional `status` |
| Attendance | `PATCH /attendance/corrections/{correction_id}` | HR; decide a correction |
| Leave | `POST /leave` | Employee/HR; submit a leave request |
| Leave | `GET /leave` | Employee/HR/Admin; list requests; optional `status`, `employee_id` |
| Leave | `GET /leave/balance` | Employee/HR; leave balances |
| Leave | `PATCH /leave/{leave_id}/cancel` | Employee/HR; cancel a request |
| Leave | `PATCH /leave/{leave_id}/decide` | HR; approve or reject a request |
| Payroll | `POST /payroll/runs` | HR; create or recalculate a monthly run |
| Payroll | `GET /payroll/runs` | Admin/HR; list runs |
| Payroll | `GET /payroll/runs/{run_id}` | Admin/HR; run details |
| Payroll | `POST /payroll/runs/{run_id}/finalize` | Admin; finalize a run |
| Payroll | `GET /payroll/payslips` | Signed-in user; employees see their own; optional `month` |
| Payroll | `GET /payslips/{payslip_id}/pdf` | Signed-in user; download permitted payslip PDF |
| Dashboard | `GET /dashboard/me` | Employee; own dashboard |
| Dashboard | `GET /dashboard/hr` | Admin/HR; HR metrics; optional `from`, `to`, `department_id` |
| Dashboard | `GET /dashboard/admin` | Admin; company metrics; optional `from`, `to`, `department_id` |
| Settings | `GET/PUT /settings` | Admin/HR read; Admin write |
| Settings | `GET/POST/PUT/DELETE /departments[/{entity_id}]` | Admin/HR read; Admin write |
| Settings | `GET/POST/PUT/DELETE /designations[/{entity_id}]` | Admin/HR read; Admin write |
| Settings | `GET/POST/PUT/DELETE /leave-types[/{entity_id}]` | Admin/HR read; Admin write |
| Settings | `POST /leave-types/defaults` | Admin; add default leave types |
| Settings | `GET/POST/PUT/DELETE /holidays[/{entity_id}]` | Admin/HR read; Admin write |
| Users | `GET /users` | Admin; list managed users |
| Users | `POST /users/hr` | Admin; create an HR login |
| Users | `PATCH /users/{user_id}/active` | Admin; enable or disable a user |
| Users | `POST /users/{user_id}/reset-password` | Admin; reset a user password |
| Communications | `GET /announcements` | Signed-in user; list announcements |
| Communications | `POST /announcements` | Admin/HR; publish an announcement |
| Communications | `GET /notifications` | Signed-in user; paginated personal notifications |
| Communications | `PATCH /notifications/{notification_id}/read` | Signed-in user; mark a notification read |
| Communications | `GET /audit` | Admin; paginated audit events and filters |
| AI | `POST /ai/chat` | Signed-in user; assistant conversation |
| AI | `POST /ai/summarize` | Signed-in user; summarize dashboard data |
| AI | `POST /ai/smart-leave` | Signed-in user; interpret a leave request |

Collection endpoints that support pagination use `page` and `page_size`; employee directory accepts `q`, `department_id`, `status`, `page`, and `page_size`. Check `/docs` for exact schemas and constraints before calling a write endpoint.

## Request examples

Check API health without credentials:

```sh
curl http://localhost:8000/api/health
```

Call an authenticated endpoint with a Supabase access token:

```sh
curl http://localhost:8000/api/me \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"
```

Successful responses are JSON and generally wrap the resource in `data`; paginated responses may also include `meta`. Errors use this shape:

```json
{
  "error": {
    "code": "forbidden",
    "message": "You do not have permission to perform this action."
  }
}
```

Validation errors may include an `error.fields` object. Common status codes are `400` validation, `401` unauthenticated, `403` forbidden, `404` not found, `409` conflict, and `5xx` service/server failure.

## Adding a feature safely

1. Start from an up-to-date `main` and use a focused feature branch. Open a PR rather than pushing directly to `main`.
2. Add or update Pydantic schemas, service/business logic, repository/database access, and a router in the relevant `backend/app/modules/<area>/` module. Keep authorization checks in the route/dependency layer and enforce employee data scoping in the service/repository too.
3. For database changes, add a reviewed, repeatable, numbered SQL migration under `supabase/migrations/` and update `supabase/schema.sql` so fresh installations match. This repo currently has no automated migration runner, so document how the migration is applied and verify it on a non-production database first. Do not make undocumented production-only schema edits.
4. Include tests for success, invalid input, role restrictions, and employee ownership/data isolation. Use the existing backend test suite and frontend build before requesting review.
5. If the frontend consumes the feature, add its API client/types and UI in the same PR where practical. Keep `VITE_API_URL` pointed at the API host plus `/api`; never expose backend secrets through a `VITE_` variable.
6. Merge only after CI/review passes. Deployments should use the same Supabase schema and compatible frontend/backend commits; verify health, sign-in, role access, and the changed feature after release.

## Local API development

From `backend/`, create/activate a virtual environment, install `requirements.txt`, configure `backend/.env` using `.env.example`, and run:

```sh
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The frontend normally runs on `http://localhost:5173`; include that exact origin in `CORS_ORIGINS`. Put local Vite values in `frontend/.env`, which Vite loads automatically. Never commit `.env`, database passwords, Supabase service-role keys, or AI provider keys. Vercel builds do not receive this ignored local file; set the same `VITE_` variables in Vercel's project environment settings and redeploy. For hosting, use the Vercel/Render/Supabase instructions in [DEPLOYMENT.md](DEPLOYMENT.md); the application is not publicly hosted just because local development works.
