# Deploy HCM Lite with Render and Vercel

This guide deploys the FastAPI backend to Render, the Vite frontend to Vercel, and keeps PostgreSQL and authentication on Supabase. It assumes the Supabase project is already set up. **Do not rerun `supabase/schema.sql` or the demo seed against the existing project.**

For API endpoints and authentication behavior, see [API_GUIDE.md](API_GUIDE.md).

## Before you start

1. Make sure the finished code is pushed to the GitHub `main` branch. Render and Vercel should deploy the same commit.
2. Rotate any database password, Supabase service-role key, or admin password that was shared in chat. Keep new values private; do not paste them into GitHub, this guide, source code, or chat.
3. From Supabase, have the project URL, a current backend service-role key, and the PostgreSQL connection string ready. Use the connection string format already expected by this project: `postgresql+asyncpg://...`. For the pooler URL in the project configuration, replace the password with the rotated database password and URL-encode special characters in it.
4. Keep `frontend/.env` for local development only. It is ignored by Git and is **not** sent to Vercel; production frontend values must be entered in Vercel.

## 1. Deploy the API on Render

1. Sign in to [Render](https://dashboard.render.com/) using the GitHub account that can access `funterpie/HCM-Lite`.
2. Choose **New** → **Blueprint** (or **Blueprint Instance**) and connect the `funterpie/HCM-Lite` repository.
3. Select branch `main`. Render should find the repository-root `render.yaml`. Review the service: it should be named `hcm-lite-api`, use the **Free** compute plan, use `backend` as its root directory, and expose the health check `/api/health`. Render spins the Free service down after 15 minutes without traffic; the first request afterward can take about a minute to wake it.
4. When Render asks for values for the Blueprint's unsynced environment variables, enter these in the Render dashboard:

   | Variable | Value |
   | --- | --- |
   | `DATABASE_URL` | The rotated-password Supabase connection string in `postgresql+asyncpg://...` format |
   | `SUPABASE_URL` | The existing Supabase project URL |
   | `SUPABASE_SERVICE_ROLE_KEY` | The rotated backend service-role key; never use the public anon key here |
   | `CORS_ORIGINS` | Temporarily `http://localhost:5173`; replace it with the Vercel production URL in step 3 |
   | `AI_API_KEY` | Optional; add the Groq API key if AI features should work |
   | `AI_MODEL` | Blueprint default is `openai/gpt-oss-120b`; change only if needed |

   `SUPABASE_JWT_SECRET` is not required for the current Supabase project's asymmetric JWT verification. Do not add `VITE_` frontend variables to Render.
5. Create the Blueprint and wait for the service deploy to finish. In the Render service page, copy its public URL, for example `https://hcm-lite-api-xxxx.onrender.com`.
6. Open `https://<your-render-service>.onrender.com/api/health`. Continue only when it returns HTTP 200 and `{"status":"ok"}`. If deployment fails, inspect that service's **Logs** and fix the first startup error before proceeding.

Render Blueprints use `render.yaml`; values marked `sync: false` are entered in the dashboard and are not stored in the repository. See [Render Blueprint documentation](https://render.com/docs/blueprint-spec) and [environment variables](https://render.com/docs/configure-environment-variables).

## 2. Deploy the website on Vercel

1. Sign in to [Vercel](https://vercel.com/dashboard) and choose **Add New** → **Project**.
2. Import the same `funterpie/HCM-Lite` GitHub repository and select `main` for production.
3. Configure the project:

   | Setting | Value |
   | --- | --- |
   | Framework preset | Vite (usually detected automatically) |
   | Root directory | `frontend` |
   | Install command | `npm ci` |
   | Build command | `npm run build` |
   | Output directory | `dist` |

   Keep the existing `frontend/vercel.json`; it handles frontend routes such as `/login` and `/admin/dashboard`.
4. Before the first production deploy, add these variables in **Project Settings** → **Environment Variables**, with **Production** selected:

   | Variable | Value |
   | --- | --- |
   | `VITE_API_URL` | `https://<your-render-service>.onrender.com/api` |
   | `VITE_COMPANY_NAME` | `Alpha Orbit` |
   | `VITE_SUPABASE_URL` | The existing Supabase project URL |
   | `VITE_SUPABASE_ANON_KEY` | The public anon/publishable key only |
   | `VITE_USE_MOCKS` | `false` |

   Never put `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, or `AI_API_KEY` in Vercel's `VITE_` variables. Any value prefixed with `VITE_` is included in browser code; only the Supabase public key belongs there.
5. Click **Deploy**. When it succeeds, copy the production domain, for example `https://hcm-lite.vercel.app`.

Vercel builds Vite environment values into the frontend, so set them **before** deploying. If you change one later, save it and make a new deployment. See [Vercel's Vite guide](https://vercel.com/docs/frameworks/frontend/vite), [build settings](https://vercel.com/docs/builds/configure-a-build), and [environment variables](https://vercel.com/docs/environment-variables).

## 3. Allow the Vercel site through API CORS

1. Return to the Render `hcm-lite-api` service and open **Environment**.
2. Replace the temporary `CORS_ORIGINS` value with the exact Vercel production origin, for example `https://hcm-lite.vercel.app`. Do not include a path or trailing slash. To allow more than one known origin, separate them with commas.
3. Save and deploy the environment change. Do not use `*` as a production origin.

## 4. Verify the deployed app

1. Confirm the Render health URL still returns HTTP 200: `https://<your-render-service>.onrender.com/api/health`.
2. Open `https://<your-vercel-domain>/login` and sign in with the existing Supabase Auth account.
3. Confirm that login redirects to the correct role dashboard and that the dashboard loads API data. A Supabase sign-in alone is not enough; the backend must also load the user's app profile.
4. Test one read-only page for each role you use. Do not use demo seed scripts on the existing production database.
5. If login says “Failed to fetch,” verify that `VITE_API_URL` is the HTTPS Render URL ending in `/api`, `CORS_ORIGINS` exactly matches the Vercel origin, and both services have redeployed after their environment variables were saved. `localhost` and `127.0.0.1` must not appear in production variables.

If confirmation or password-reset email links are added later, configure the deployed domain in Supabase Auth URL settings as well.

## Future updates

After the initial GitHub connections, pushes or merges to `main` trigger deployments. For new work, use a feature branch and pull request, run the frontend build and backend tests, then merge after review. Vercel can create preview deployments for branches; keep production credentials restricted to the production environment.

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

Set `VITE_API_URL=http://localhost:8000/api`, `VITE_COMPANY_NAME`, `VITE_SUPABASE_URL`, the public `VITE_SUPABASE_ANON_KEY`, and `VITE_USE_MOCKS=false` in `frontend/.env`. Never put the backend service-role key in frontend variables.
