# Local Demo and Deployment

## Supabase

1. Run `supabase/schema.sql` once on a fresh Supabase project.
2. Configure the backend environment from `backend/.env.example` with the Supabase URL, service-role key, JWT secret, and transaction-pooler database URL.
3. Start the backend and complete the first-run setup at `http://localhost:5173/setup`. This creates the company settings and first admin through Supabase Auth.
4. To add non-login sample employees and dashboard activity, run `supabase/demo_seed.sql` against that configured database. It is idempotent and refuses to run before setup; it does not replace existing rows.

The demo employees do not have login accounts. Create real employee logins through the HR employee-registration screen.

## Local development

Backend, from `backend/`:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, from `frontend/`:

```sh
npm ci
npm run dev
```

Set `VITE_API_URL=http://localhost:8000/api`, `VITE_SUPABASE_URL`, and the public `VITE_SUPABASE_ANON_KEY` in `frontend/.env.local`. Keep `VITE_USE_MOCKS=false` for the real API. Never put the service-role key in frontend variables.

## Deployment checks

- Backend start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Frontend build command: `npm ci && npm run build`; publish `frontend/dist` with the frontend host.
- Configure all backend secrets in the backend host and the Supabase URL/public anon key in the frontend host.
- Keep the database service-role connection private to the backend. Rotate any previously exposed Supabase service-role key and database password before production deployment.
- Run `npm run build` and the backend tests before release. The first-run setup is intended for a fresh database; do not use the demo seed on a production database.
