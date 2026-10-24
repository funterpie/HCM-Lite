# ABDULLAH: Infra/DevOps, AI assistant (M8), HR logins, dashboard API layer, payslip PDF, README  (NO SQL)

Read `PROJECT.md` first. Everything there is binding. This file is your task list.
(Updated split: Taha owns all SQL and the database. You never write SQL. You call the functions he and Saqib expose.)

## You own (only you edit these)
- Render, Vercel, env vars, the Groq key, the README
- `modules/ai/*`
- `modules/users/*` (HR login endpoints; calls Taha's `create_employee_for_user` and the Supabase Admin API, no SQL)
- `modules/dashboards/router.py`, `service.py`, `schemas.py` (the API on top of Taha's query functions in `repo.py`)
- `modules/payroll/pdf.py`
- Optional if ahead: CSV export (Python only)

## Task checklist (times from the 4-hour start)
- [ ] A1 (0:00-0:10) Create the Supabase project in the dashboard (clicks only). Turn OFF "confirm email". Share URL, anon key, service-role key, pooler connection string, and whether JWKS or legacy JWT secret, **privately, never in git**. Tell Taha, who runs `schema.sql`.
- [ ] A2 (0:10-0:25) Render backend service (root `backend/`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`), env vars, `/health` ping every 5-10 min
- [ ] A3 (0:10-0:25) Vercel frontend project + `VITE_*` vars, add Vercel URL to `CORS_ORIGINS`
- [ ] A4 (0:25-0:40) Groq key (Render env `AI_API_KEY`, never in a chat), choose `AI_MODEL` that supports tool calling, run the smoke test script
- [ ] A5 (0:40-1:20) `/ai/chat` Groq tool loop + the 7 tools. Use stub services until the real ones land (signatures in PROJECT.md section 10)
- [ ] A6 (1:20-1:40) HR logins: `POST /users/hr`, `PATCH /users/{id}/active`, `POST /users/{id}/reset-password` (needs Taha's T4 and T6 function)
- [ ] A7 (1:40-1:55) AI guardrails: 15 s timeout, 20/hour limit via Taha's `core/ai_log.py` helpers, friendly fallbacks, log every call
- [ ] A8 (1:55-2:20) `/ai/summarize`, `/ai/smart-leave`, policy Q&A, Roman Urdu line
- [ ] A9 (2:20-2:45) Dashboard API: router/service/schemas for `GET /dashboard/hr|admin|me` wrapping Taha's `dashboards/repo.py` functions
- [ ] A10 (2:45-2:55) Swap AI tool stubs for the real service functions and check AI answers equal dashboard numbers
- [ ] A11 (2:55-3:15) Payslip PDF with ReportLab + `GET /payslips/{id}/pdf` (own only for Employee)
- [ ] **3:15 FEATURE FREEZE**
- [ ] A12 (3:15-3:45) README, fresh-install rehearsal, judges' test questions
- [ ] A13 (3:45-4:00) Submit both links on lms.saylaniit.com (test in incognito first)

## Rules you must not break
- Never write SQL or touch `schema.sql`. Need a new query or column? Ask Taha.
- The browser never talks to Groq. The model never touches the database. Tools call service functions with the caller's scope.
- AI answers must equal the dashboard numbers. Both use the same service functions.
- Never commit or paste secrets. Check `.gitignore` for `.env`.

## First prompt to paste into your AI coding tool
```
Read PROJECT.md and ABDULLAH.md. Build backend/app/modules/ai/ with a Groq tool-calling loop (OpenAI-compatible API, httpx, base URL
https://api.groq.com/openai/v1, model from env AI_MODEL, key from AI_API_KEY, 15 second timeout).
Define tools get_headcount, get_attendance_summary, get_late_comers, get_leave_summary, get_my_leave_balance, get_payroll_summary,
search_employees as thin wrappers around service functions that take the current user and respect scoped_employee_id.
Employees must be refused when asking about another person's data or salary. Use stubbed service functions until the real ones
are merged; keep the signatures in PROJECT.md section 10. Do NOT write any SQL.
```

## Definition of done
- All three URLs live, `/health` stays warm, CORS correct.
- Judges' test questions answer correctly and match the dashboard. The salary question is refused.
- "Next Monday and Tuesday off for my sister's wedding" returns correct dates and the casual leave type.
- README is complete and both links are submitted.
