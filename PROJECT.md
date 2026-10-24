# HCM Lite: shared project file

Every teammate's AI tool must read this file first, then its own `<NAME>.md`.
If this file and a personal file disagree, **this file wins**. Change it only by telling the whole team.

Saylani Hackathon, 24 Oct 2026. Hard deadline: **4 hours from start**. Submit on lms.saylaniit.com: public Git repo link and live hosted link.

---

## 1. What we are building

A web-based Human Capital Management system with three roles (Admin, HR, Employee) and an AI assistant that answers from real data. The system **starts empty**. There is no dummy data. Judges install fresh, create the company, and check that dashboards and AI answers match what they entered.

Web app is required. Android APK via Capacitor is a stretch goal (see section 12).

## 2. Stack (fixed, do not swap)

| Layer | Choice |
|---|---|
| Frontend | Vite + React + TypeScript + Tailwind CSS, SPA, hosted on Vercel |
| Backend | FastAPI (Python 3.11), Pydantic v2, SQLAlchemy 2 async, hosted on Render |
| Database + Auth | Supabase (Postgres + Supabase Auth) |
| AI | Groq API with tool calling, key only in the backend env (`AI_API_KEY`), model in `AI_MODEL` |
| PDF | ReportLab |
| Tests | pytest, rule services only (about 15 tests) |
| Mobile (stretch) | Capacitor wrapping the same React build |

Design language: ultra-minimal, high contrast, clean typography, distraction-free. One accent color. No gradients, no clutter.

## 3. Repo layout (monorepo)

```
hcm-lite/
  PROJECT.md  SAQIB.md  TAHA.md  ABDULLAH.md  FARHAN.md  README.md
  supabase/schema.sql
  backend/
    app/
      main.py
      core/        config.py  security.py  deps.py  errors.py  audit.py
      db.py
      rules/       pure functions: working_days, attendance_status, payroll, tax
      modules/     auth settings employees attendance leave payroll dashboards ai comms
                   (each: router.py  service.py  repo.py  schemas.py)
    tests/
    requirements.txt  .env.example
  frontend/
    src/  api/  components/  pages/{admin,hr,employee}/  lib/  App.tsx
    .env.example
```

Layers: `router (HTTP, auth deps) -> service (rules, permissions) -> repo (SQL)`. Rules never live in routers.

## 4. Git workflow

- One repo, `main` is always deployable. Branches: `taha/*`, `saqib/*`, `abdullah/*`, `farhan/*`.
- Small PRs (or direct merge if you agree on a voice call), merge to `main` at least every 30 minutes.
- Never commit `.env`. Commit `.env.example` only.
- Folder ownership is in each personal file. Don't edit a file you don't own. Ask the owner.

## 5. Environment variables

Backend (`backend/.env.example`):
```
DATABASE_URL=postgresql+asyncpg://...      # Supabase pooler string
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=                        # only if project uses legacy HS256; else use JWKS
AI_API_KEY=
AI_MODEL=                                   # a Groq model that supports tool calling; check Groq docs
CORS_ORIGINS=http://localhost:5173,https://<vercel-app>.vercel.app
ADMIN_EMAIL=                                # optional first-run shortcut
ADMIN_PASSWORD=
```
Frontend (`frontend/.env.example`):
```
VITE_API_URL=
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

**asyncpg + Supabase pooler gotcha:** with the transaction pooler (port 6543) create the engine with `connect_args={"statement_cache_size": 0}`.
**Render gotcha:** the free tier sleeps when idle. Add `GET /health` and ping it every 5-10 min (cron-job.org or UptimeRobot). Open the app 5 minutes before the demo.
Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## 6. Auth and access (M1)

- Frontend logs in with `supabase-js` and sends `Authorization: Bearer <access_token>` to FastAPI. The frontend uses Supabase **only for auth**. All data goes through FastAPI.
- FastAPI verifies the token, then loads `profiles` to get `role`, `is_active` and `must_change_password`. **Never trust a role from the token.**
- `deps.py` exposes: `current_user`, `require_role("admin","hr")`, and `scoped_employee_id(user)`, which returns the user's own `employee_id` for Employees and `None` (meaning "all") for Admin/HR.
- Every query for Employee-visible data **must** go through the scope helper. Hiding a button is not security.
- Temp-password flow: HR registers an employee, and the backend calls the Supabase Admin API `create_user(email, temp_password, email_confirm=true)` and inserts `profiles(must_change_password=true)`. Frontend forces a change-password screen until the flag clears (`POST /auth/change-password` flips it).
- First run: `POST /setup` is allowed only while `settings` is empty. It creates the settings row and the Admin (Admin API). If `ADMIN_EMAIL`/`ADMIN_PASSWORD` are set, create that Admin on boot when no admin exists.
- The default leave types (annual 14, sick 8, casual 10, unpaid unlimited) are offered as an **"Add default leave types" button** in Admin setup. Nothing is auto-seeded.

## 7. Business rules (exact, from the brief)

**Settings:** office start 09:00, grace 15 min, half day under 5 h, weekend Sat+Sun (ISO weekdays 6,7), office lat/lng + radius 150 m. Stored as settings, applied to **new** records only. All "today" and time-of-day logic uses `settings.timezone` (default `Asia/Karachi`).

**Attendance:**
- Server stamps the time, never the client. One record per employee per day. Second check-in = **409**.
- `late` if check-in is after start + grace (09:15). `present` otherwise.
- On check-out: if worked hours < 5 then `half_day`; else keep `present`/`late`.
- `missing_checkout` = has check-in, no check-out, and the day is over.
- `absent` = working day (not weekend, not holiday), employee active on that date, no record, no approved leave, date already passed.
- `on_leave` = approved leave covers the date.
- Absent and missing_checkout are **computed, not stored** (no cron on free hosting). Single source of truth: `rules.daily_status(...)` used by dashboards, payroll and AI. Never re-implement it elsewhere.
- Corrections: Employee requests with reason, HR approves/rejects. On approve, upsert the attendance row with `source='correction'` and recompute status.

**Leave:**
- Working days only (skip weekends and holidays).
- Quotas: annual 14, sick 8, casual 10, unpaid unlimited.
- Overlap with another pending/approved request, or days over remaining balance = **422**.
- Balance = quota minus approved days in the calendar year. **Computed, never stored.**
- Employee may cancel own pending (or future approved) leave. HR approves/rejects with a comment. Both send an in-app notification.

**Payroll (monthly):**
- Gross = 1.5 x basic (HRA 40%, medical 10% of basic).
- Per day = gross / working days in the month.
- Deduction = per_day x (absent days + unpaid leave days + 0.5 x half days).
- Prorate joiners/leavers: count only working days between join_date and exit_date inside the month.
- Tax (illustrative) on **annual gross = gross x 12**, then divide by 12 for the month:
  - 0 to 600,000: 0
  - 600,000 to 1,200,000: 5% of the part above 600,000
  - 1,200,000 to 2,400,000: 30,000 + 15% of the part above 1,200,000
  - 2,400,000 to 3,600,000: 210,000 + 25% of the part above 2,400,000
  - above 3,600,000: 510,000 + 35% of the part above 3,600,000
- Net = gross - deduction - monthly tax. (Decision: tax is computed on full gross, not on gross after deduction. Document in README.)
- HR creates/reviews a draft run. **Only Admin finalizes.** Finalized runs are locked (DB trigger + service check).

**Employees:** HR registers with job details and salary, which creates the login. Server-side search, filters, paging. CSV import has a dry run returning `row + field + reason` and checks required fields, unique code/email, valid email, known department, ISO date, salary > 0.

**Audit log:** actor, action, entity, before/after JSON for every create/update/approve/finalize. Append-only (DB rules). Use `core/audit.py::log(...)` from services.

## 8. Roles and permissions (checklist)

| # | Functionality | Admin | HR | Employee |
|---|---|---|---|---|
| 01 | First-run setup | Manage | - | - |
| 02 | Login, logout, change password, role menus | Own | Own | Own |
| 03 | Company settings | Manage | View | - |
| 04 | Departments, designations, leave types, holidays | Manage | View | - |
| 05 | Create HR logins, deactivate/reset any login | Manage | - | - |
| 06 | Register employee, edit details | View | Manage | Own phone and address |
| 07 | Directory, search, Employee 360 | All | All | Own |
| 08 | CSV import (dry run) and export | - | Manage | - |
| 09 | Check in / out | - | Own | Own |
| 10 | Attendance calendar and daily board | All | All | Own |
| 11 | Attendance correction | View | Approve | Request |
| 12 | Apply/cancel leave, balance, history | - | Own | Own |
| 13 | Approve/reject leave with comment | View | Approve | - |
| 14 | Salary structure | View | Manage | - |
| 15 | Payroll draft: create and review | View | Manage | - |
| 16 | Finalize payroll | Manage | - | - |
| 17 | Payslips + PDF | All | All | Own |
| 18 | Dashboards | Company | HR | Personal |
| 19 | AI chat | All data | HR data | Own data |
| 20 | AI dashboard summary | Yes | Yes | - |
| 21 | Smart leave | - | Own | Own |
| 22 | Policy Q&A | Yes | Yes | Yes |
| 23 | Announcements | Post | Post | Read |
| 24 | Notifications | Own | Own | Own |
| 25 | Audit log | View | - | - |

HR is also an employee of the company: HR has an employee record too, so rows 09, 12 and 17 apply to HR for their own data.

## 9. API contract

Base path `/api`. JSON only. Dates ISO (`YYYY-MM-DD`), timestamps ISO 8601 UTC.

**Success:** `{ "data": ... }`. Lists: `{ "data": [...], "meta": { "page", "page_size", "total" } }`. Query `?page=1&page_size=20`.
**Error:** `{ "error": { "code": "string", "message": "string", "fields": { "field": "reason" } } }`
Status codes: 400 validation, 401 not logged in, 403 wrong role/scope, 404, **409 duplicate check-in**, **422 leave overlap / over balance**, 429 AI rate limit.

| Module | Endpoint | Roles |
|---|---|---|
| M1 | `POST /setup` `{company_name, admin_email, admin_password}` | public, once |
| M1 | `GET /me` -> `{id, email, role, employee_id, must_change_password}` | all |
| M1 | `POST /auth/change-password` `{new_password}` | all |
| M2 | `GET/PUT /settings` | Admin PUT, HR GET |
| M2 | `GET/POST/PUT/DELETE /departments`, `/designations`, `/leave-types`, `/holidays` | Admin write, HR read |
| M2 | `POST /leave-types/defaults` (adds the four default types) | Admin |
| M2 | `POST /users/hr`, `PATCH /users/{id}/active`, `POST /users/{id}/reset-password` | Admin |
| M3 | `GET /employees?q&department_id&status&page` | Admin, HR |
| M3 | `POST /employees`, `PUT /employees/{id}` | HR |
| M3 | `PATCH /me/profile` `{phone, address}` | Employee |
| M3 | `GET /employees/{id}` (360: profile, attendance summary, leave balances, last payslip) | Admin, HR, own |
| M3 | `POST /employees/import?dry_run=true` (multipart CSV), `GET /employees/export` | HR |
| M4 | `POST /attendance/check-in`, `POST /attendance/check-out` | Employee, HR (own) |
| M4 | `GET /attendance?from&to&employee_id` (calendar; Employee forced to own) | all |
| M4 | `GET /attendance/board?date&department_id` | Admin, HR |
| M4 | `POST /attendance/corrections`, `GET /attendance/corrections?status`, `PATCH /attendance/corrections/{id}` `{decision, comment}` | Employee request, HR decide |
| M5 | `POST /leave` `{leave_type_id, start_date, end_date, reason}` | Employee, HR (own) |
| M5 | `PATCH /leave/{id}/cancel`, `GET /leave?status&employee_id`, `GET /leave/balance` | per scope |
| M5 | `PATCH /leave/{id}/decide` `{decision: "approved"\|"rejected", comment}` | HR |
| M6 | `PUT /employees/{id}/salary` `{basic_salary}` | HR |
| M6 | `POST /payroll/runs` `{month}` (creates/recomputes draft), `GET /payroll/runs`, `GET /payroll/runs/{id}` | HR create, Admin view |
| M6 | `POST /payroll/runs/{id}/finalize` | Admin only |
| M6 | `GET /payslips?month`, `GET /payslips/{id}/pdf` | all (own for Employee) |
| M7 | `GET /dashboard/admin`, `/dashboard/hr`, `/dashboard/me` with `?from&to&department_id` | by role |
| M8 | `POST /ai/chat` `{message, history?}` -> `{answer, tool_used?}` | all |
| M8 | `POST /ai/summarize` `{dashboard: "hr"\|"admin", from, to, department_id}` -> `{bullets: [..]}` | Admin, HR |
| M8 | `POST /ai/smart-leave` `{text}` -> `{leave_type_id, start_date, end_date, reason}` (never saves) | Employee, HR |
| M9 | `GET/POST /announcements` | all read, Admin/HR post |
| M9 | `GET /notifications`, `PATCH /notifications/{id}/read` | own |
| M9 | `GET /audit?actor&entity&page` | Admin |
| - | `GET /health` | public |

Key payloads:
```
POST /attendance/check-in  -> 201 {data:{date, check_in, status}}   | 409 {error:{code:"already_checked_in"}}
POST /leave                -> 201 {data:{id, days, status:"pending"}} | 422 {error:{code:"overlap"|"insufficient_balance"}}
GET  /leave/balance        -> {data:[{leave_type_id, name, quota, used, remaining}]}
GET  /dashboard/hr         -> {data:{kpis:{headcount, present, on_leave, late_today, pending_approvals},
                              attendance_trend:[{date, rate}], absenteeism_by_dept:[{department, pct}],
                              leave_by_type:[{type, days}], top_late:[{employee, count}]}}
POST /payroll/runs         -> {data:{id, month, status:"draft", payslips:[{employee_id, gross, deduction, tax, net, ...}]}}
```

Frontend types are generated from FastAPI's OpenAPI (`npx openapi-typescript <API>/openapi.json -o src/api/schema.d.ts`). Taha keeps Pydantic schemas accurate, so schemas are the contract.

## 10. Shared function signatures (pure, in `backend/app/rules/`)

Saqib writes these first. Everyone else imports them and never re-implements the logic.

```python
working_days(start: date, end: date, holidays: set[date], weekend: set[int]) -> list[date]
attendance_status(check_in: datetime|None, check_out: datetime|None, s: Settings) -> str   # present|late|half_day|missing_checkout
daily_status(employee, day: date, record, approved_leave: bool, holidays, s) -> str|None   # None = not a working day
compute_tax_monthly(gross_monthly: Decimal) -> Decimal
compute_payslip(employee, month: date, daily_statuses: list[str], unpaid_days: int, s) -> PayslipDict
leave_balance(quota: int|None, approved_days: int) -> int|None
haversine_m(lat1, lng1, lat2, lng2) -> float      # camera attendance bonus
```

## 11. Metrics (computed on the server with SQL aggregation; filterable by date range and department)

| Metric | Formula |
|---|---|
| Headcount | active + probation on the end date |
| Attrition | exits in period / average headcount x 100 |
| Attendance rate | (present + late + missing_checkout + 0.5 x half_day) / (working-day records - on_leave) |
| Late % | late / (present + late) |
| Absenteeism | absent days / expected working days, per department |
| Leave utilization | approved days / quota, per leave type and department |
| Payroll cost | sum of gross and net by month and department |
| Average salary | mean gross by department and designation |

Dashboard KPIs: **HR:** headcount, present, on leave, late today, pending approvals, attendance trend, absenteeism by dept, leave by type, top 5 late-comers, AI summary. **Admin:** headcount, attrition YTD, payroll cost, avg salary, headcount by dept, payroll cost by dept, gender and tenure, audit feed, AI summary. **Employee:** check-in widget, hours this week vs 40, late count, leave balance, last payslip, announcements, ask-my-assistant.

## 12. AI assistant (M8) rules

- `POST /ai/chat`: the model picks a tool, the backend runs it **with the caller's scope**, the model writes the answer.
- Tools (reuse the same services as REST, never raw SQL from the model): `get_headcount`, `get_attendance_summary`, `get_late_comers`, `get_leave_summary`, `get_my_leave_balance`, `get_payroll_summary`, `search_employees`.
- Employee asking for someone else's salary or data: the tool layer refuses and the assistant says so politely.
- Dashboard summary: send the KPI JSON for the current filters, get 3-5 bullets using **only** those numbers.
- Smart leave: "need next Monday and Tuesday off for a wedding" -> validated JSON `{type, start, end, reason}` -> pre-filled form. Retry once on invalid JSON, then return an error so the UI shows the normal form. **The AI never saves anything.** Pass today's date and weekday in the prompt so "next Monday" resolves correctly.
- Policy Q&A: the rules in section 7 sit in the system prompt. Answer only from them, or say "I don't know".
- Guardrails: 15 s timeout with a friendly fallback, 20 requests per user per hour (429), every call logged in `ai_logs`, answers labelled "AI-generated" in the UI.
- Bonus (cheap): add one line to the system prompt so it understands Roman Urdu.

## 13. Build order and clock (T = start of the 4 hours)

| Time | Goal |
|---|---|
| T+0:00 to 0:30 | Supabase created and `schema.sql` run (Abdullah). Backend skeleton deployed to Render with `/health`, frontend skeleton on Vercel (Abdullah + Taha + Farhan). Taha pushes `core/` (auth deps, errors, db). Saqib pushes `rules/` with tests. Farhan pushes design system and shells with mocked data. |
| T+0:30 to 1:30 | M1 to M3 (Taha). M4, M5 (Saqib). Infra done, then M7 service (Abdullah). Login, setup, employee pages, check-in, leave pages (Farhan). First end-to-end: setup, register employee, check in. |
| T+1:30 to 2:30 | Payroll (Taha endpoints, Saqib calc), payslip PDF (Abdullah), `/ai/chat` plus tools (Abdullah). Dashboards, payroll and payslip screens (Farhan). |
| T+2:30 to 3:15 | Smart leave, summarize, policy Q&A, notifications, audit view, announcements. Bonus items **only if** the core demo already works. |
| **T+3:15 FEATURE FREEZE** | No new features. Bug fixes only. |
| T+3:15 to 3:45 | Full fresh-install rehearsal using the demo script below, README, hosted links tested in an incognito window. |
| T+3:45 to 4:00 | Submit both links on the LMS. Do not wait for the last minute. |

Cut order if behind: camera/APK first, then CSV import (keep export), then bonus items, then dark mode. Never cut: login per role, check-in, leave approval, payroll finalize, dashboards, AI chat, smart leave, audit log.

Stretch (only if core is demo-ready by T+2:30): Capacitor APK (`npx cap add android`, build in Android Studio) and camera check-in (MediaPipe face detector in the WebView, `@capacitor/geolocation`, server does the Haversine check, reject on no face / multiple faces / outside radius / GPS accuracy worse than 100 m, store the result not the photo).

## 14. Demo script (5 minutes, judges follow this)

1. Fresh install: Admin does setup (company, office hours, location), adds a department and leave types, creates an HR login.
2. HR registers 2-3 employees. One signs in, changes the password, checks in.
3. Employee types a leave request in plain words and confirms the pre-filled form. HR approves.
4. HR opens the dashboard, clicks Summarize, and asks the assistant who is on leave. HR runs payroll for the month. Admin finalizes.
5. Employee downloads the payslip and asks for a colleague's salary (refused). Admin shows the audit log.

Judges' live questions: "How many active employees in {department}?", "Who came late most often this month?", "What is this month's attendance rate?" (must match the dashboard), "How many sick leaves do I have left?", "What is {colleague}'s salary?" (refuse), "I need next Monday and Tuesday off for my sister's wedding" (pre-filled casual leave, correct dates).

## 15. Scoring (what we are optimizing)

Core HR flows 25, Data and analytics 20, AI 15, Code quality 15 (module structure, rules in services, validation, tests), UI/UX 10 (loading, empty, error states, responsive 375px+), Security and RBAC 10, Demo and docs 5. Bonus +10.

## 16. README must contain

Stack, how to run locally, how to create the first Admin, how to set `AI_API_KEY`, the payroll tax decision (section 7), what is done and what is not. Hosted link opens on first-run setup.

## 17. Definition of done (whole project)

The demo script in section 14 runs start to finish on the hosted links, from an empty database, with no manual database edits, and the dashboard numbers equal the AI answers.
