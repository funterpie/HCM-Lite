# FARHAN: Frontend lead (UI/UX, client state, responsiveness)

Read `PROJECT.md` first. Everything there is binding. This file is your task list.

## You own (only you edit these)
- Everything in `frontend/`
- Capacitor setup, if we reach the stretch goal

## Design language (non-negotiable)
Ultra-minimal, high contrast, clean typography, distraction-free.
- One typeface (Inter or system UI), two weights. One accent color. White and near-black surfaces. No gradients, no shadows beyond a hairline border.
- Generous spacing, large touch targets, **responsive from 375 px up**.
- Every screen needs **loading, empty and error states**. Judges check this.
- Optional bonus: dark mode via Tailwind `dark:` classes (cheap if colors are tokens from day one).
- AI output always shows an "AI-generated" label.

## Step 1 (first 30 min)
1. Scaffold Vite + React + TypeScript + Tailwind in `frontend/`. Add `react-router`, `@supabase/supabase-js`, `@tanstack/react-query`, `recharts`.
2. Design tokens (colors, spacing, type scale) and base components: Button, Input, Select, Card, Table, Modal, Badge, Toast, Skeleton, EmptyState, ErrorState.
3. `src/api/client.ts`: a typed `fetch` wrapper that adds the Supabase access token, unwraps `{data}`, and throws `{error:{code,message,fields}}`. Add a `VITE_USE_MOCKS=true` mode with mocked responses from PROJECT.md section 9, so you are never blocked on the backend.
4. Auth: Supabase login screen, session handling, `GET /me` after login, **force change-password screen when `must_change_password` is true**, role-based redirect, route guards.
5. Once Taha's backend is live: `npx openapi-typescript <API_URL>/openapi.json -o src/api/schema.d.ts` and use those types.

## App shells
- Admin menu: Dashboard, Setup (company, departments, designations, leave types, holidays), Logins, Employees, Payroll (view and **Finalize**), Announcements, Audit log, AI assistant
- HR menu: Dashboard, Employees (register, edit, salary, CSV), Attendance board, Corrections, Leave inbox, Payroll (draft), Announcements, AI assistant
- Employee menu: Dashboard, Check in/out, My attendance (calendar + request correction), Leave (apply, balance, history), Payslips, Profile (phone, address), Announcements, AI assistant
- HR also gets the Employee check-in and leave pages for their own data.
- Notifications bell in the top bar.

## Task checklist
- [ ] Shells + guards + login + first-run `/setup` screen (the hosted URL must open on setup when the DB is empty: call `POST /setup` flow when `GET /me`-less bootstrap says setup is needed; ask Taha for a `GET /setup/status` if you need it)
- [ ] Admin setup screens (settings with office location + radius, departments, designations, leave types with "Add defaults" button, holidays), logins screen
- [ ] HR: register employee form (field-level errors from `error.fields`), employee list with search/filter/paging, Employee 360, salary editor
- [ ] Employee: check-in widget (one big button, shows status and time), attendance calendar, correction request
- [ ] Leave: apply form, balance cards, history, HR approval inbox with comment
- [ ] **Smart leave box:** textarea -> `POST /ai/smart-leave` -> pre-filled form the user confirms (never auto-submits)
- [ ] Payroll screens: HR create/review draft table, Admin finalize button with confirm, locked state after finalize, payslip list + PDF download
- [ ] Dashboards: HR, Admin, Employee with date range and department filters, charts (Recharts), "Summarize" button -> AI bullets
- [ ] AI chat panel (all roles): message list, loading state, AI-generated label, friendly fallback text on 429/timeout
- [ ] Announcements, notifications, audit log table (Admin)
- [ ] Bonus if time: dark mode, PWA manifest
- [ ] Stretch only after T+2:30: `npm i @capacitor/core @capacitor/cli @capacitor/android`, `npx cap init`, set `webDir: 'dist'`, `npx cap add android`; camera check-in per PROJECT.md section 13

## Rules you must not break
- Never put the AI key or service-role key in the frontend. Only the Supabase **anon** key.
- UI hiding is for UX only. Assume the backend enforces access. Still, never show another role's menu items.
- Show server validation messages from `error.fields` next to the right inputs.
- Use the exact status values from the API (`present`, `late`, `half_day`, `absent`, `missing_checkout`, `on_leave`).

## First prompt to paste into your AI coding tool
```
Read PROJECT.md and FARHAN.md. Scaffold frontend/ with Vite + React + TypeScript + Tailwind.
Design language: ultra-minimal, high contrast, one accent color, clean typography, responsive from 375px.
Build design tokens and base components (Button, Input, Select, Card, Table, Modal, Badge, Toast, Skeleton, EmptyState, ErrorState).
Build src/api/client.ts (Supabase token -> Bearer header, unwrap {data}, throw {error}) with a VITE_USE_MOCKS mode using the payloads in PROJECT.md section 9.
Then build Supabase login, role-based routing (admin/hr/employee shells with the menus in FARHAN.md), and a forced change-password screen when must_change_password is true.
Every page must have loading, empty and error states.
```

## Definition of done
- All three roles log in and see only their own menu.
- Every screen works at 375 px.
- The full demo script in PROJECT.md section 14 can be clicked through on the hosted link.
