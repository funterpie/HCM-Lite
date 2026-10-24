# HCM Lite: FINAL GUIDE (everything in one place)

Saylani Hackathon, 24 Oct 2026, Zaitoon Ashraf IT Park. **4 hours from start.** Submit on https://lms.saylaniit.com/ (Git repo link + hosted link).
Repo: https://github.com/funterpie/HCM-Lite.git

This file is the map. Details live in the files listed in section 2. If two files disagree, `PROJECT.md` wins.

---

## 1. What we are building

An AI-assisted Human Capital Management web app for **Admin, HR and Employee**. It starts **empty** (no dummy data). Judges install fresh, create the company and a few employees, and check that dashboards and AI answers match what they entered.

Must work end to end: first-run setup, login per role, employees, check-in/out, leave with approval, monthly payroll with payslip PDF, dashboards, AI assistant (chat, summarize, smart leave, policy Q&A), announcements, notifications, audit log.

## 2. Files and what they are for

| File | Use |
|---|---|
| `FINAL_GUIDE.md` | This map. Read first. |
| `PROJECT.md` | **The contract:** stack, rules, permissions, API, metrics, AI rules. Every AI tool must read it. |
| `GIT_GUIDE.md` | Where to push/pull, stubs when a teammate hasn't pushed, conflicts. |
| `TAHA.md`, `SAQIB.md`, `ABDULLAH.md`, `FARHAN.md` | Each person's ownership, checklist, first prompt. |
| `guides/<NAME>_GUIDE.txt` | Step-by-step task prompts. Works with any AI account. |
| `guides/TAHA_GPT_MASTER_PROMPT.txt` | One paste-in prompt to set up GPT for Taha's work. |
| `supabase/schema.sql` | Database schema (run once). `views.sql` is written by Taha (task D2). |
| `progress/<NAME>.txt` | One line per finished task, committed to git (for resuming on another AI account). |

## 3. Team and ownership (only edit what you own)

| Person | Owns |
|---|---|
| **Taha** | Backend foundation and **ALL SQL/database**: `main.py`, `core/*`, `db.py`, `schema.sql`, `views.sql`, auth/setup, org setup, employees, payroll endpoints, comms/audit, `dashboards/repo.py` |
| **Saqib** | `rules/*` (pure functions + pytest), attendance, leave, payroll maths and payroll input helper |
| **Abdullah** | Infra (Supabase project clicks, Render, Vercel, Groq key), `modules/ai/*`, HR logins, dashboard API layer, payslip PDF, README, submission. **Writes no SQL.** |
| **Farhan** | All of `frontend/` (Lovable or any tool) |

## 4. Stack (fixed)

Frontend: Vite + React + TypeScript + Tailwind (Vercel). Backend: FastAPI + Pydantic v2 + SQLAlchemy 2 async (Render). DB + Auth: Supabase. AI: Groq with tool calling, called only from the backend. PDF: ReportLab. Tests: pytest on the rule functions. Optional stretch: Capacitor Android APK, camera attendance.

Design: ultra-minimal, high contrast, clean typography, one accent color, responsive from 375 px, loading/empty/error states everywhere.

## 5. Accounts and keys (who does what, before coding)

| Item | Who | Note |
|---|---|---|
| GitHub repo + collaborators | Taha (done) | Make sure everyone accepted the invite. Public, or shared with judges. |
| Supabase project | Taha created it and ran `schema.sql` | Turn OFF "Confirm email". |
| Share keys **privately** | Taha, then to Abdullah and the team | Project URL, anon key, service-role key, pooler connection string, JWKS-or-legacy-secret. **Never in git or an AI chat.** |
| Render service | Abdullah | Root `backend/`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Ping `/health` every 5-10 min. |
| Vercel project | Abdullah | Root `frontend/`, three `VITE_*` vars, add the URL to `CORS_ORIGINS`. |
| Groq key | Abdullah | Only in Render env as `AI_API_KEY`; choose `AI_MODEL` that supports tool calling. |
| Local `.env` files | Everyone | On your own machine only; `.env.example` is committed. |

Environment variables are listed in `PROJECT.md` section 5.

## 6. The first 35 minutes (do in this order)

1. **Taha** pushes the project files and `.gitignore` to `main` (commands in `GIT_GUIDE.md`). Everyone clones and creates `<name>/work`.
2. **Taha T1** (0:00-0:10): FastAPI skeleton, `/health`, empty `router.py` in every module, all routers already included in `main.py`. Push to `main`.
3. **Abdullah A2/A3** (0:10-0:25): Render + Vercel deploy from `main`; post the URLs.
4. **Taha T2** (0:15-0:35): errors, JWT verify, `current_user`, `require_role`, `scoped_employee_id`. Push and say "core is in".
5. **Saqib S1-S4** (0:00-0:30): `rules/` + tests. Push and say "rules are in".
6. **Farhan F1** (0:00-0:20): design system and base components, then API client with mocks.

## 7. Clock by person (times from the start)

| Time | Taha | Saqib | Abdullah | Farhan |
|---|---|---|---|---|
| 0:00 | T1 skeleton | S1-S3 rules + tests | A1 keys, Render/Vercel | F1 design system |
| 0:15 | D1 done, T2 core | S4 leave/geo rules | A2/A3 deploy, A4 Groq test | F2 API client + mocks + auth |
| 0:35 | T3 helpers, T4 setup/auth | S5 check-in/out | A5 AI chat (stub tools) | F3 login, setup, routing |
| 1:05 | T5 org setup | S6 calendar + board | (A5 continues) | F4 shells, F5 Admin setup |
| 1:25 | T6 employees | S7 corrections | A6 HR logins | F5/F6 employees |
| 1:55 | D2 view + HR dashboard SQL | S8 leave apply/balance | A7 guardrails, A8 summarize/smart leave | F6 employees |
| 2:20 | T7 payroll endpoints | S9 leave decisions | A9 dashboard API layer | F7 check-in, F8 leave + smart leave |
| 2:50 | D3 admin/me SQL, T8 comms | S10 payroll inputs | A10 real services in AI, A11 PDF | F9 HR pages, F10 payroll |
| 3:15 | **FREEZE** (Taha: D4 parity check) | S12 rehearsal | A13 README, rehearsal | F11-F13 (UI only), F14 polish |
| 3:45 | Final merge | Final merge | A14 submit | Final merge |

**Farhan is the bottleneck.** Several of his tasks overlap, and F11 to F13 run to about T+3:25 (UI only, with the backend frozen). Saqib is free after S10 (about 2:55) and Abdullah after A11. They should take pages from Farhan's list (for example F9 HR pages, F13 announcements and audit) and send them via Lovable prompts.

## 8. Git in 6 lines (full version in `GIT_GUIDE.md`)

```bash
git checkout <name>/work && git pull origin main        # start of every task
# ...do the task, test it...
git status && git diff --stat                           # only YOUR files should show
git add <your folders> && git commit -m "T4: setup + auth" && git push origin <name>/work
git checkout main && git pull origin main && git merge <name>/work && git push origin main
git checkout <name>/work && git merge main              # then post "merged T4" in chat
```
Merge after every finished task and at least every 30 minutes. **Already built code before the repo was ready? See `GIT_GUIDE.md` section 5** (copy your files into the right folders, push your branch, then merge). Never force-push. Never commit `.env`. If a teammate hasn't pushed what you need, **use a stub with the agreed signature** (`PROJECT.md` section 10) and keep moving.

## 9. Who calls whom (interfaces)

| Function | Written by | Used by |
|---|---|---|
| `current_user`, `require_role`, `scoped_employee_id` | Taha | everyone |
| `audit.log`, `notify`, `ai_log.log_ai_call`, `ai_log.count_ai_calls_last_hour` | Taha | Saqib, Abdullah |
| `employees.service.create_employee_for_user(session, user_id, data, role)` | Taha | Abdullah (HR logins) |
| `settings.service.list_leave_types(session)` | Taha | Abdullah (smart leave) |
| `payroll.service.get_payslip(session, payslip_id)` | Taha | Abdullah (PDF) |
| `dashboards/repo.py` query functions | Taha | Abdullah (dashboard API, AI tools) |
| `rules/*`, `get_attendance_summary`, `get_leave_summary`, `get_my_leave_balance`, `payroll_inputs` | Saqib | Taha (payroll), Abdullah (AI, dashboards) |
| Generated TypeScript types from `/openapi.json` | Taha's schemas | Farhan |

## 10. Rules cheat sheet (exact version in `PROJECT.md` section 7)

- **Attendance:** server time (Asia/Karachi). One record per day (second check-in = 409). Late after 09:15 (09:15 itself is not late). Half day under 5 h. **Absent and missing_checkout are computed, never stored.**
- **Leave:** working days only. Quotas annual 14, sick 8, casual 10, unpaid unlimited. Overlap or over-balance = 422. Balance is computed.
- **Payroll:** gross = 1.5 x basic. Per day = gross / working days. Deduction = per day x (absent + unpaid + 0.5 x half days). Prorate joiners/leavers. Tax on annual gross with the slab table, monthly = annual / 12. Net = gross - deduction - tax. HR drafts, **only Admin finalizes**, finalized runs are locked.
- **Access:** role always comes from the `profiles` table, never the token. Employees only see their own rows. HR can't change settings, create Admins or finalize payroll.
- **Audit:** every create/update/approve/finalize logs actor, action, entity, before/after. Append-only.
- **Responses:** `{data}` / `{error:{code,message,fields}}`. Codes: 400 validation, 401, 403, 404, 409 duplicate, 422 rule, 429 AI limit.

## 11. AI assistant rules (Abdullah)

- Groq tool calling, from the backend only. The model never touches the database and never saves anything.
- Tools reuse the same services as the REST API: headcount, attendance summary, late-comers, leave summary, my leave balance, payroll summary, search employees.
- Employee asking for someone else's salary or data: politely refused.
- Dashboard summary uses only the KPI numbers it is given. Smart leave returns validated JSON `{leave_type_id, start_date, end_date, reason}`; one retry, then the normal form. Policy Q&A answers only from the rules in the system prompt.
- 15 s timeout with a friendly fallback, 20 requests per user per hour, every call logged, answers labelled "AI-generated". Roman Urdu understanding is a one-line bonus.
- **AI answers must equal dashboard numbers**, because both call the same functions.

## 12. If your AI quota runs out

1. Open another AI or account (Gemini, ChatGPT, DeepSeek, Claude free tier).
2. Paste the **START PROMPT** from your guide file, then the **RESUME PROMPT**, and attach your `progress/<NAME>.txt` and only the files for the next task.
3. One task per chat. Ask for changed files only. Never paste real keys.
4. Keep `progress/<NAME>.txt` updated and committed.

## 13. Cut order if you fall behind

1. Camera attendance and the Capacitor APK (stretch only)
2. CSV import, then CSV export
3. Bonus items (late penalty rule, dark mode, PWA)
4. **Never cut:** login per role, check-in, leave approval, payroll finalize, dashboards, AI chat, smart leave, audit log, README, hosted links.

## 14. Freeze, rehearsal, submission

- **T+3:15 FEATURE FREEZE.** Only bug-fix merges. Farhan's UI-only finishing work may run to about 3:25.
- **T+3:15-3:45:** everyone runs the full demo on the **hosted** links against a **fresh database** (drop and re-run `schema.sql` and `views.sql`). Taha also compares `v_daily_status` with Saqib's `daily_status` on about five cases.
- **T+3:45-4:00:** README final, repo clean (`.env.example` only), both links tested in an incognito window, then submit on the LMS. Do not wait for the last minute.

**5-minute demo script (judges follow this)**
1. Fresh install: Admin sets up the company, office hours and location, a department and leave types, and creates an HR login.
2. HR registers 2-3 employees. One signs in, changes the password, and checks in.
3. Employee types a leave request in plain words and confirms the pre-filled form. HR approves.
4. HR opens the dashboard, clicks Summarize, and asks the assistant who is on leave. HR runs payroll for the month. Admin finalizes.
5. Employee downloads the payslip and asks for a colleague's salary (refused). Admin shows the audit log.

**Judges' live questions:** "How many active employees in {department}?", "Who came late most often this month?", "What is this month's attendance rate?" (must match the dashboard), "How many sick leaves do I have left?", "What is {colleague}'s salary?" (refuse), "I need next Monday and Tuesday off for my sister's wedding" (pre-filled casual leave, correct dates).

## 15. Submission checklist

- [ ] Repo is public or shared with the judges; README has stack, how to run, how to create the first Admin, how to set `AI_API_KEY`, the payroll tax decision, what is done and not done
- [ ] No real keys in git (only `.env.example`); history checked for `.env`
- [ ] Hosted web link opens on first-run setup when the database is empty
- [ ] Backend `/health` is warm (ping running) and CORS includes the Vercel URL
- [ ] All three roles log in and see only their own menu
- [ ] Demo script passes on the hosted link from an empty database
- [ ] AI test questions answer correctly and match the dashboard; the salary question is refused
- [ ] Both links submitted on https://lms.saylaniit.com/ in everyone's own portal, as the brief requires ("every student logs in to their own portal and shares two links")

## 16. Scoring (what we optimize)

Core HR flows 25, Data and analytics 20, AI 15, Code quality 15, UI/UX 10, Security and RBAC 10, Demo and docs 5, plus up to 10 bonus.

## 17. Troubleshooting

| Problem | Fix |
|---|---|
| Backend errors with asyncpg on the Supabase pooler | Engine needs `connect_args={"statement_cache_size": 0}` |
| Render app is slow on the first request | Free tier sleeps. Ping `/health` every 5-10 min and open the app 5 minutes before the demo. |
| Browser shows a CORS error | Add the exact Vercel URL (and `http://localhost:5173`) to `CORS_ORIGINS` on Render, then redeploy |
| New users can't log in right after creation | Turn off "Confirm email" in Supabase Auth, or create users with `email_confirm=true` |
| 401 on every request | Wrong token check. Use JWKS if the project has new signing keys, else the legacy HS256 secret. Check which your project uses. |
| AI call fails | Check `AI_API_KEY`, and that `AI_MODEL` supports tool calling. Test with `groq_smoke_test.py`. |
| AI says a different number than the dashboard | One of them isn't using the shared service function. Fix the AI tool to call it. |
| Schema change needed | Tell Taha. He changes the live DB and `schema.sql` together so a fresh install still works. |
| Merge conflict | See `GIT_GUIDE.md` section 5. Keep your own files, ask the owner for theirs. |
| Lovable code isn't in the repo | Farhan copies it into `frontend/` at T+1:30, 2:45 and 3:15 (see `GIT_GUIDE.md` section 8) |

## 18. Never

- Force-push, or commit `.env`, keys, `.venv/`, `node_modules/`
- Paste real keys into any AI chat
- Edit a file you don't own, or put business rules in a router
- Merge to `main` without running your part once
- Add features after the freeze
