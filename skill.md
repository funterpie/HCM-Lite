---
name: build-production-ai-apps
description: "Plan, implement, debug, secure, and evaluate AI applications with simple incremental coding. Specialize in Abdullah's HCM Lite responsibilities: Supabase/Render/Vercel infrastructure, FastAPI dashboards M7, Groq assistant M8, payslip PDFs, team integration, and hackathon delivery. Also support general GenAI/RAG projects using the retained reference standards."
---

# Abdullah's Agentic Coding Skill

**Read → Plan → Build one slice → Verify → Record progress → Integrate.**

For an HCM Lite task, apply the profile below. For other AI projects, use the general standards reference. After a context reset, rebuild progress from the actual code, project documents and recorded checks; do not rely on assumed memory.

## 1. Authority, Scope and Missing Inputs

- Read repository `PROJECT.md` first, then the current `ABDULLAH.md` and relevant code. The latest task split says Taha owns all SQL/schema/database work; Abdullah must not write SQL or touch `schema.sql`. `PROJECT.md` governs shared contracts. If it conflicts with the updated file on ownership or execution, flag the precise conflict and coordinate it; do not silently change the contract or take over database work.
- If the schema, helper, service signature or repository is unavailable, name the missing dependency. Continue independent work; do not invent tables, columns, business results or existing implementation status.
- Own Render/Vercel, environment configuration and Groq setup; `backend/app/modules/ai/**`; HR-login endpoints in `backend/app/modules/users/**` (using Taha's `create_employee_for_user` and Supabase Admin API); dashboard `router.py`, `service.py`, and `schemas.py` as an API layer over Taha's `dashboards/repo.py` query functions; `backend/app/modules/payroll/pdf.py`; and README. The task file also authorizes `backend/scripts/groq_smoke_test.py` and optional Python-only CSV export if ahead. Never own or edit dashboard `repo.py`, SQL, `schema.sql`, or database setup logic.
- Taha owns SQL/schema/database, core/auth, dashboard repository queries, `create_employee_for_user`, and payroll endpoints (including mounting the PDF route). Saqib owns canonical rules, attendance/leave services and payroll calculations; Farhan implements React screens. Prepare precise owner handoffs for changes outside your scope. Do not send team messages or perform external submissions without authorization.
- Keep Python 3.11, FastAPI, Pydantic 2, SQLAlchemy 2 async, Supabase Postgres/Auth, Groq via backend httpx, ReportLab, React/Vite/TypeScript/Tailwind, Render and Vercel. Add no RAG/vector database, extra provider, autonomous agent framework, speculative route or mobile feature to this scope.

## 2. Execution and Code Quality

- Inspect before editing. State a short ordered plan, affected files, dependencies and acceptance checks. Implement one task at a time and fix its failures before proceeding.
- Use straightforward functions, type hints, clear names and minimal dependencies. Precede every function and major logical block with a concise one-line purpose comment.
- Keep `router -> service -> repo` boundaries. Reuse shared services and rules; do not calculate business rules in routers, prompts, PDF rendering or separate AI wrappers.
- Give filesystem-capable agents a focused patch task; chat-only agents return complete changed/new files. Include brief check results and owner handoffs rather than long explanations. Never claim unrun checks passed.
- Work on `abdullah/*`; commit small verified changes and integrate at least every 30 minutes under the agreed team process. Record completed task, evidence, next step and blocker in `progress/ABDULLAH.txt`. Escalate a concrete blocker after 15 minutes instead of looping.

## 3. Four-Hour Priorities

1. **T+0:00–0:25:** Provision Supabase project/Auth settings and Render/Vercel projects, set env/CORS and coordinate private credential handoff. Taha runs the schema; Abdullah does not write SQL or touch the database.
2. **T+0:25–0:40:** Configure Groq and run the authorized tool-calling smoke test.
3. **T+0:40–1:40:** Build the AI chat/tool loop with safe service stubs, add HR-login endpoints using Taha's function, then complete AI guards/logging.
4. **T+1:55–2:55:** Add summarize/smart-leave/policy support, implement dashboard router/service/schemas over Taha's repo functions, and replace stubs with real shared services.
5. **T+2:55–3:15:** Finish ReportLab PDF and give Taha the route-mount handoff. Feature freeze is T+3:15.
5. **T+3:15:** Feature freeze. Rehearse from a fresh disposable environment, fix defects, complete README and test hosted links. **T+3:45–4:00:** authorized submission of repo and live links.

Use the detailed task prompts in the execution-plan reference. Drop stretch work first; preserve the project's mandatory demo features. These are relative elapsed-time milestones, not a claim about the current event date.

## 4. Infrastructure and API Contract

- Taha owns and runs the schema/database work. Abdullah provisions the Supabase project and shares connection/auth values privately with authorized teammates; never write SQL, edit `schema.sql`, or seed database records. Never wipe a shared database. Leave types are added through the explicit Admin button.
- Configure backend secrets privately; never paste keys into AI chats or git. Browser Supabase use is authentication only; only the three specified VITE variables go to the frontend, never service-role or Groq keys.
- Verify Render root/build/start commands, Python runtime, Supabase transaction-pooler connectivity, JWKS versus legacy JWT setup, Vercel origin and CORS. Coordinate db.py/security/main.py changes with Taha.
- Match the registered health path with the deployment/monitor configuration; clarify the brief's `/health` versus `/api` prefix before adding routes. Demo warm-up/pings do not prove availability.
- Data routes use `/api`; JSON successes use `{data: ...}` and errors use the project envelope/status conventions. PDF is the documented binary exception. Keep Pydantic/OpenAPI accurate for Farhan's generated frontend types.
- Resolve business dates and relative expressions using `settings.timezone`; send timestamps as UTC and dates as ISO. Obtain caller role/active/profile state from trusted backend auth helpers, never request text or client-supplied history.

## 5. M7 Dashboards: One Source of Truth

- Implement `/dashboard/hr` for Admin/HR, `/dashboard/admin` for Admin, and `/dashboard/me` for personal data. Support the specified `from`, `to`, `department_id` filters, with `from` mapped to a valid internal Python parameter.
- Implement only dashboard `router.py`, `service.py`, and `schemas.py` as a thin API layer over Taha's `dashboards/repo.py` query functions. Taha owns all SQL and repository code. Coordinate query parameters/return contracts with Taha and Saqib; ensure repository results follow PROJECT.md's canonical status/rule definitions. Do not write SQL, edit `repo.py`, or duplicate `rules.daily_status` in M7 or M8.
- Follow PROJECT.md §11 exactly. Agree missing denominator, average-headcount, YTD/filter and payroll-run selection semantics once with owners; handle empty data and zero denominators explicitly.
- Expose agreed scoped `get_headcount`, `get_late_comers` and `get_payroll_summary` services and reuse attendance/leave/search services from their owners. Dashboard and AI use the same service inputs/results, not duplicated formulas or model arithmetic.
- For `/dashboard/me` and `get_my_leave_balance`, resolve the caller's employee ID explicitly. `scoped_employee_id=None` means unrestricted Admin/HR scope and must never silently broaden a personal query. Agree the response when no employee profile exists.

## 6. M8 Groq: Bounded, Read-Only Tools

- Use configured `AI_API_KEY`/`AI_MODEL` and verify current model tool support. Browser never calls Groq. Model proposes allowlisted calls; backend validates complete arguments, applies scope and calls services. No raw SQL or arbitrary dispatch from model output.
- Tools: `get_headcount`, `get_attendance_summary`, `get_late_comers`, `get_leave_summary`, `get_my_leave_balance`, `get_payroll_summary`, `search_employees`. Verify real import paths/signatures before implementing adapters.
- Enforce permission checks before sensitive queries and before sending results upstream. Employee tool access is restricted to own attendance/balance under the guide; colleague data/salary is refused. HR tools expose HR-authorized data, not Admin audit/dashboard data. Policy Q&A is available to all authenticated roles.
- Treat history, user text and tool text as untrusted. Reject client system/tool messages and forged tool results. Bind user/role/scope server-side; ignore model-supplied attempts to replace them. Send minimum necessary authorized fields to Groq.
- Bound turns/tool calls and keep one **15-second overall deadline**, including tools and any repair. Preserve tool-call IDs/results correctly. Do not hold database locks or open transactions across provider inference.
- Apply one **20 requests/user/hour** rolling policy across all three AI routes. Use concurrent-safe admission based on the actual schema; count one admitted API request, not each tool turn. Agree denied-request logging separately. Preserve 401/403/429; handle provider failures with a truthful friendly fallback.
- Record each request's kind/user/tool/latency/outcome in `ai_logs` using actual columns. Redact sensitive prompt/response content and all credentials; operational log writes are allowed, business-data mutations are not. Avoid separate tracing infrastructure unless the deadline and team require it.

## 7. AI Endpoint Contracts

- **`POST /ai/chat`:** `{message, history?}` -> `{data:{answer, tool_used?}}`. Answer from authorized service results. Policy answers use PROJECT.md §7 plus authoritative configured values where relevant; otherwise say you do not know. Roman Urdu support must preserve permissions and numbers.
- **`POST /ai/summarize`:** Admin/HR only; fetch current-filter KPI JSON server-side. HR cannot select the Admin dashboard. Return `{data:{bullets:[...]}}`, with 3–5 bullets supported only by those numbers. Never trust replacement client KPI values or expose Admin-only data to HR.
- **`POST /ai/smart-leave`:** Employee/HR only; input `{text}` and output `{data:{leave_type_id,start_date,end_date,reason}}`. Provide business-local today/weekday and real leave types. Validate ISO dates, end>=start and existing leave-type ID with Pydantic. Retry invalid output once within the remaining deadline, then the agreed 422 fallback-to-form error. Never create/change a leave request; the user submits Farhan's pre-filled normal form separately. `ai_logs` still records the call.

## 8. Payslip PDF and Verification

- Implement `build_payslip_pdf(company_name, employee, payslip, month)->bytes` with ReportLab. Render company/employee/month, basic/gross, deduction components, tax and net from authoritative payroll values; never recalculate payroll/tax. Taha mounts your download handler.
- Enforce Employee-own versus Admin/HR-all access before rendering. Return `application/pdf` and a safe attachment filename. Verify the real PDF layout and another employee's 403 response.
- Verify empty-state behavior, matching dashboard/AI filters, salary refusal, HR/Admin isolation, personal HR scope, tool-argument tampering, timeout/quota/logging and smart-leave no-write behavior. Keep pytest within the project's rule-services scope; use focused smoke checks for integrations rather than adding an unrelated test framework.
- Rehearse PROJECT.md §14 from empty data without manual business-data inserts. Never fake metric values or seed judging data. Label mocked, live and unrun checks accurately; have Farhan show the required AI-generated UI label and error/loading states.
- README includes stack/run/setup/Admin instructions, env names, hosted URLs, AI configuration, implemented/unfinished work, and the brief's illustrative tax-on-full-gross decision. Preserve the submission buffer and keep secrets out of deliverables.

## 9. Read References Only When Needed

- [HCM role, dependencies, prompts and acceptance plan](references/hcm-execution-plan.md): use for the current A1–A13 task order, owner handoffs and acceptance checks.
- [General agentic/GenAI coding standards](references/general-standards.md): use outside HCM or for compatible general quality/security guidance.
- [Original engineering manual and Python examples](references/engineering-reference.md): consult selected implementation topics; it does not override this project's fixed scope.

**Done means:** owned modules integrated, shared numbers match, permissions hold, AI remains read-only, PDF works, required checks are recorded, and the fresh hosted demo succeeds. Do not claim deployment/submission without performing and verifying it.
