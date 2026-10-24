# ABDULLAH: Infra/DevOps, dashboards (M7), AI assistant (M8), payslip PDF

Read `PROJECT.md` first. Everything there is binding. This file is your task list.

## You own (only you edit these)
- Supabase project, Render service, Vercel project, env vars, the README
- `modules/dashboards`, `modules/ai`
- `modules/payroll/pdf.py` (ReportLab payslip), plus the `GET /payslips/{id}/pdf` route (Taha wires the router, you write the function)

## Step 1 (first 30 min, everyone is blocked on you)
1. Create the Supabase project. Run `supabase/schema.sql` in the SQL editor.
2. Share the keys **in a private chat, never in git**: `SUPABASE_URL`, anon key, service-role key, DB pooler connection string (transaction pooler), and whether the project uses JWKS or the legacy JWT secret.
3. Supabase Auth settings: turn **off** email confirmation, so Admin-API-created users can log in immediately.
4. Create the Render web service from the repo (root `backend/`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Add all env vars. Confirm `/health` works.
5. Create the Vercel project from `frontend/` with the three `VITE_*` vars.
6. Add a 5-10 minute ping on `/health` (cron-job.org or UptimeRobot) so Render doesn't sleep during judging.
7. Create the Groq key and put it in Render as `AI_API_KEY`. Pick `AI_MODEL` from the models on Groq's docs page that **support tool calling**.

## Task checklist
- [ ] Infra above, then post the three URLs in the team chat
- [ ] Dashboards: `GET /dashboard/hr|admin|me` with `from`, `to`, `department_id`. Every number computed in SQL aggregation using Saqib's `daily_status`. Formulas in PROJECT.md section 11. Expose service functions (`get_headcount`, `get_late_comers`, `get_payroll_summary`...) because AI tools reuse them.
- [ ] `POST /ai/chat`: Groq tool calling loop. Tools: `get_headcount`, `get_attendance_summary`, `get_late_comers`, `get_leave_summary`, `get_my_leave_balance`, `get_payroll_summary`, `search_employees`. Each tool executes **with the caller's scope**. An Employee asking for another person's salary is refused politely.
- [ ] `POST /ai/summarize`: send KPI JSON, return 3-5 bullets, prompt says "use only these numbers"
- [ ] `POST /ai/smart-leave`: return JSON `{leave_type_id, start_date, end_date, reason}`. Put today's date and weekday plus the real `leave_types` in the prompt. Validate with Pydantic, retry once, then return an error. **Never save anything.**
- [ ] Policy Q&A: PROJECT.md section 7 rules in the system prompt, "answer only from these rules or say you don't know"
- [ ] Guardrails: 15 s timeout with friendly fallback, 20 req/user/hour (429), every call in `ai_logs`, key only in the backend env
- [ ] Payslip PDF with ReportLab: company name, employee, month, gross, deductions, tax, net. Employee can only download their own (403 otherwise).
- [ ] README (see PROJECT.md section 16)
- [ ] Bonus (cheap): Roman Urdu line in the system prompt

## Rules you must not break
- The browser never talks to Groq. The model never touches the database. Tools call services.
- AI answers must equal dashboard numbers. Both use the same service functions.
- Don't commit secrets. Check `.gitignore` for `.env`.

## First prompt to paste into your AI coding tool
```
Read PROJECT.md and ABDULLAH.md. Build backend/app/modules/ai/ with a Groq tool-calling loop
(model from env AI_MODEL, key from AI_API_KEY, 15 second timeout, per-user rate limit of 20/hour, log every call to ai_logs).
Define tools get_headcount, get_attendance_summary, get_late_comers, get_leave_summary, get_my_leave_balance,
get_payroll_summary, search_employees as thin wrappers around service functions that take the current user and
enforce scoped_employee_id for Employees. Employees must be refused when asking about another employee's data.
Add /ai/chat, /ai/summarize (uses only the KPI JSON given) and /ai/smart-leave (validated Pydantic JSON, one retry, never saves).
Use stubbed service functions until Saqib and Taha merge theirs; keep the signatures in PROJECT.md.
```

## Definition of done
- All three URLs live, `/health` stays warm, CORS correct.
- Judges' test questions all answer correctly and match the dashboard. The salary question is refused.
- "Next Monday and Tuesday off for my sister's wedding" returns correct dates and the casual leave type.
