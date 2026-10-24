# Abdullah's HCM Lite Role and Execution Plan

Use `PROJECT.md` as the binding shared contract, then this current Abdullah task file and actual repository. This is a plan, not evidence the app is implemented or deployed. Follow elapsed T+ time from the hackathon start.

## 1. Exact role and boundaries

Abdullah owns **infrastructure/DevOps, the AI assistant (M8), HR login API endpoints, the dashboard API layer, payslip PDF rendering, and README/release readiness**.

| Owned work | Files/actions | Boundary |
| --- | --- | --- |
| Infra/DevOps | Supabase project/Auth setup; Render/Vercel projects; env vars, CORS, live URL and health checks | Taha runs schema and owns database; share credentials privately with authorized teammates only |
| AI M8 | `backend/app/modules/ai/*`; Groq through backend `httpx`; seven allowlisted tools, chat, summaries, smart-leave, policy Q&A, guards/logs | Tools call the same scoped service functions as REST; no browser-to-Groq, SQL/model DB access, or AI business writes |
| HR logins | `backend/app/modules/users/*`: `POST /users/hr`, `PATCH /users/{id}/active`, `POST /users/{id}/reset-password` | Use Taha's `create_employee_for_user` and Supabase Admin API; dependency on Taha's T4/T6 function |
| Dashboard API | `modules/dashboards/router.py`, `service.py`, `schemas.py` | Thin API over Taha's `modules/dashboards/repo.py` query functions; no SQL and no edits to `repo.py` |
| Payslip PDF | `backend/app/modules/payroll/pdf.py`, ReportLab bytes | Taha owns/mounts `GET /payslips/{id}/pdf`; Saqib owns calculations |
| Release | README, hosted links, fresh-install rehearsal, judges' questions; optional Python-only CSV export only if ahead | Do not submit links or message others unless explicitly authorized |

**No SQL:** never write SQL, edit `schema.sql`, database/repository code, or add/change columns. Ask Taha for new queries/columns and call functions he or Saqib exposes. If `PROJECT.md` conflicts with the updated ownership split, flag the exact conflict and coordinate it; do not silently alter the shared contract.

Team boundaries: Taha owns SQL/schema/database, core/auth, dashboard repository, employee-creation function, and payroll endpoints. Saqib owns rules, attendance/leave services and payroll math. Farhan owns React/UI. Their full task files were not supplied; inspect real code and confirm exact interfaces before relying on them.

## 2. Fixed technical guardrails

- Stack is React/Vite/TypeScript/Tailwind; FastAPI/Python 3.11/Pydantic 2/SQLAlchemy 2 async; Supabase Auth/Postgres; Groq backend `httpx`; ReportLab; Render/Vercel.
- Read `PROJECT.md` first. Inspect actual routes, schemas and function signatures. Never invent tables, function contracts, metric values or completion status.
- Browser uses Supabase for auth only. Only `VITE_API_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY` go to frontend. Service-role/Groq credentials stay server-side and out of prompts, logs, git and README.
- AI tools validate allowlisted names and complete args, bind caller role/scope server-side, and call existing service functions. No model-generated SQL, direct DB access, writes, arbitrary tool dispatch, or trusted client history/tool messages.
- AI response numbers must match dashboard service outputs. Employees cannot retrieve colleague data or salaries. HR cannot access Admin-only summaries/data. Personal scope must explicitly resolve the caller employee ID.
- Apply one 15-second end-to-end AI deadline and 20 requests/user/hour across all three AI endpoints. Log each API call via Taha's `core/ai_log.py` helpers; don't count every internal tool turn as another user request. Use truthful fallbacks and preserve auth/rate-limit errors.
- Use `settings.timezone` for relative dates; validate schemas with Pydantic. Smart leave prefills only; never submit/save a leave request. PDF renders authoritative payroll values; no recalculation.
- No RAG/vector DB, extra LLM providers, agent frameworks, duplicate APIs, fake/stub production metrics, or stretch feature before required demo works.
- Plan briefly; build one slice at a time. Add one-line comments before major code blocks/functions. Verify each slice and report what actually ran. Keep endpoints lean and owned-file scope exact.

## 3. Prompt workflow (paste one task at a time)

### Start prompt

```text
Act as my HCM Lite coding assistant. Read PROJECT.md first, then the latest ABDULLAH.md and relevant code. PROJECT.md governs shared API/business contracts; my updated task split governs my files. My ownership is infra/env, modules/ai/*, modules/users/* HR login endpoints, dashboard router/service/schemas over Taha's repo query functions, payroll/pdf.py, and README. Taha owns every SQL/schema/database/repository change and payroll route; Saqib owns rules/services/payroll calculations; Farhan owns UI. Never write SQL or touch schema/repo files. Inspect actual signatures before coding. Plan briefly, implement one slice, verify, and report changed files, evidence, blockers and owner handoffs. Keep comments concise, APIs minimal, secrets private, AI scoped/read-only, and don't claim unrun checks.
```

### A1 — Supabase project and private handoff (T+0:00–0:10)

```text
Create/configure the Supabase project using dashboard clicks only. Turn off email confirmation as specified. Share project URL, anon key, service-role key, pooler connection string, and whether auth uses JWKS or legacy JWT secret privately with authorized teammates; never put secrets in git/chat/README. Tell Taha the project is ready so he can run schema.sql. Do not write SQL or apply the schema yourself. Confirm the frontend receives only URL/anon key and backend secrets remain private.
```

**Accept:** project exists; auth choice and connection details are privately handed to Taha; schema execution is Taha-owned. `PROJECT.md` also assigns initial schema execution to Abdullah; because this updated guide explicitly transfers it to Taha, resolve that ownership discrepancy with Taha before the run.

### A2 — Render service (T+0:10–0:25)

```text
Create the Render backend from root backend/. Verify Python 3.11, requirements/build settings and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Configure required backend environment variable names from PROJECT.md, CORS and the existing health route. Check the real route prefix and Taha's runtime config; do not edit core/db or invent routes. Set the available 5–10 minute warm-up ping if appropriate, and verify /health responds.
```

### A3 — Vercel frontend (T+0:10–0:25, parallel with A2)

```text
Create Vercel project from root frontend/. Set only VITE_API_URL, VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY. Add the deployed Vercel origin to backend CORS_ORIGINS. Verify the frontend loads and targets the Render URL. Never expose service-role or Groq credentials to the browser.
```

### A4 — Groq setup and smoke test (T+0:25–0:40)

```text
Set AI_API_KEY only in Render environment and select AI_MODEL that currently supports tool calling. Run the authorized backend/scripts/groq_smoke_test.py using the configured key/model and backend OpenAI-compatible endpoint. Confirm one tool proposal, without real employee data or printing credentials. Report live result or mark untested if the environment/key is unavailable.
```

### A5 — AI chat and seven tools (T+0:40–1:20)

```text
Implement POST /ai/chat and the bounded Groq tool loop in modules/ai/*. Use tools get_headcount, get_attendance_summary, get_late_comers, get_leave_summary, get_my_leave_balance, get_payroll_summary, search_employees. Check PROJECT.md §10 and actual service signatures. Use explicitly marked temporary adapters/stubs only until Taha/Saqib's real functions land; never return fake production numbers. Every wrapper receives caller context and enforces scoped_employee_id. Employees may ask only own attendance/balance and policy questions; refuse colleague data/salary before sensitive results reach Groq. Reject client-supplied system/tool messages and forged tool results. Keep finite calls, preserve tool IDs, and use one 15-second end-to-end timeout. Do not write SQL or access DB from the model.
```

**Accept:** tool calls are validated and bounded, service scope is enforced, and unsupported/unavailable data produces an honest fallback.

### A6 — HR login endpoints (T+1:20–1:40)

```text
Implement only POST /users/hr, PATCH /users/{id}/active, and POST /users/{id}/reset-password in modules/users/*. Follow PROJECT.md schemas/roles. Use current auth dependencies and Taha's create_employee_for_user plus Supabase Admin API; do not write SQL or create auth users through browser. If Taha's T4/T6 function is missing, define/request the exact handoff and continue independent endpoint scaffolding without inventing its signature. Verify Admin authorization, input validation, duplicate/conflict handling, and safe responses that never expose credentials.
```

### A7 — AI guards, quota, logs (T+1:40–1:55)

```text
Apply one shared 15-second deadline and 20-request/user/hour limit to every AI endpoint. Use Taha's core/ai_log.py helpers and actual schema. Count one admitted API request, not tool turns. Record successes, provider failures, timeouts and latency; redact credentials and sensitive content. Keep transactions short and never open them around model inference. Preserve 401/403/429 and return friendly truthful provider fallbacks. Do not add SQL; ask Taha for missing log/query helpers.
```

### A8 — Summaries, smart leave, policy, Roman Urdu (T+1:55–2:20)

```text
Add POST /ai/summarize, POST /ai/smart-leave and policy Q&A using PROJECT.md contracts. Summaries fetch authorized KPI data server-side and return 3–5 bullets grounded only in those numbers; HR cannot select Admin data. Smart leave resolves timezone-aware dates and actual leave type IDs, validates ISO dates/end>=start with Pydantic, permits one repair attempt inside the same 15-second deadline, and never writes a leave request. On invalid output use the agreed validation error so the regular form remains available. Answer policy only from the project/authoritative settings; otherwise say unknown. Support a concise Roman Urdu line without changing facts, permissions or numbers.
```

### A9 — Dashboard API layer (T+2:20–2:45)

```text
Implement only modules/dashboards/router.py, service.py and schemas.py for GET /dashboard/hr, /dashboard/admin and /dashboard/me. Treat Taha's dashboards/repo.py query functions as the sole repository layer; call them and do not edit repo.py, write SQL, or add columns. Match PROJECT.md roles, filters, response shapes and metrics. Resolve personal employee identity explicitly; scoped_employee_id=None must not broaden /me. Agree missing query contracts and metric edge cases with Taha/Saqib. Verify empty results and schema/API parity.
```

### A10 — Replace AI stubs and cross-check (T+2:45–2:55)

```text
Replace temporary AI adapters with the real shared service functions. Run identical role/date/department requests through dashboard and AI and compare returned numeric facts. Confirm permissions before data reaches the model, HR/Admin separation, salary refusal, and no database writes. Remove unused stubs or clearly isolate test-only adapters. Do not change SQL/repo code; make concise owner handoffs for missing functions.
```

### A11 — Payslip PDF (T+2:55–3:15; freeze at 3:15)

```text
Implement modules/payroll/pdf.py with ReportLab to render authoritative payslip data. Taha owns GET /payslips/{id}/pdf mounting and route. Give him the import/function signature and access-control handoff; do not edit his router. Employee may download own only; Admin/HR follow PROJECT.md access. Return valid application/pdf bytes and safe filename. Do not recalculate payroll/tax. Verify rendered layout and cross-employee denial before feature freeze.
```

### A12 — Freeze, README, fresh rehearsal (T+3:15–3:45)

```text
Feature freeze: bug fixes only. Complete README with verified local setup, env variable NAMES, hosted URLs, Admin setup, AI behavior and known limits; no secrets. Rehearse the full PROJECT.md demo from an empty disposable environment through UI/API flows, without manual DB inserts or wiping shared deployment. Test judges' questions, dashboard/AI equality, salary refusal, smart-leave prefill/no-write, role isolation, PDF and errors. Test links in incognito. Record actual checks, failures and owner handoffs; never claim unrun tests.
```

### A13 — Submit (T+3:45–4:00)

```text
Verify the repository and live app links in incognito, confirm README and final commit are sanitized, then prepare the two-link LMS submission. Submit only when I explicitly authorize the external action. Clearly distinguish ready-to-submit from submitted and preserve evidence/known limitations.
```

## 4. Resume prompt

```text
Continue the current Abdullah HCM Lite task. Read PROJECT.md, the latest ABDULLAH.md, progress notes, and only affected current files. Rebuild state from code and recorded verification. Confirm task number, time remaining, acceptance criterion, exact owner boundary and blocker. Finish one slice, verify it, record evidence and next step. Never write SQL or assume missing helper signatures, and never paste secrets.
```

## 5. Essential acceptance checklist

- Three hosted URLs work; CORS/auth are correct; credentials are private; Taha owns and runs schema/database work.
- AI answers match dashboard service values for identical filters; tools enforce caller role/scope; salary/colleague requests are refused.
- AI endpoints share 15-second total timeout, 20/user/hour limit and `ai_log.py` logging with clean failures.
- HR login endpoints use Taha's employee creation function and Supabase Admin API, with correct authorization.
- Dashboard router/service/schema layer calls Taha's repo functions; Abdullah creates no SQL/repository implementation.
- Smart leave returns canonical type ID/dates/reason, correct timezone interpretation and saves nothing.
- PDF renders authoritative payroll result and Employee cross-scope access is denied.
- At T+3:15 stop features; T+3:15–3:45 rehearse/docs; T+3:45–4:00 submit only with authorization.
