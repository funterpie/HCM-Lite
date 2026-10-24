# HCM Lite

A web-based Human Capital Management system with three roles (Admin, HR, Employee) and an AI assistant answering from real data. Built for the Saylani Hackathon.

## Stack
- **Frontend:** Vite + React + TypeScript + Tailwind CSS (Hosted on Vercel)
- **Backend:** FastAPI (Python 3.11), Pydantic v2, SQLAlchemy 2 async (Hosted on Render)
- **Database + Auth:** Supabase (Postgres + Supabase Auth)
- **AI Assistant:** Groq API (`AI_API_KEY`, model `AI_MODEL`) with backend tool calling and 15s timeout
- **PDF Generation:** ReportLab for payslips

---

## Local Development Setup

### 1. Backend (`backend/`)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Fill in your Supabase & Groq credentials
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (`frontend/`)
```bash
cd frontend
npm install
cp .env.example .env      # Fill in VITE_API_URL and Supabase public keys
npm run dev
```

---

## First-Run Admin Setup & AI Configuration
- **First Admin:** On fresh boot when no settings exist, POST `/setup` or configure `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the backend environment variables.
- **AI Key:** Set `AI_API_KEY` in the Render environment variables (never commit keys to git).

---

## Payroll Tax Decision (PROJECT.md §7)
Tax is computed on **annual gross (`gross x 12`)**, divided by 12 for the monthly deduction, calculated on the full gross salary prior to attendance deductions.

---

## What is Done & Hosted Links
- **Backend & AI Module (M8):** Chat with 7 allowlisted tools, rate-limiting (20 req/hr), ai_logs, summaries, smart leave, and policy Q&A with Roman Urdu support.
- **Users & HR Logins (M2):** Admin HR creation via Supabase Admin API and employee profiles.
- **Dashboards (M7):** Admin, HR, and Employee dashboard API endpoints.
- **Payslip PDF:** ReportLab payslip generation and scoped downloads.
- **Hosted Links:**
  - Frontend (Vercel): [HCM Lite Frontend](https://<vercel-app>.vercel.app)
  - Backend (Render): [HCM Lite API](https://<render-app>.onrender.com/health)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude Code <noreply@anthropic.com>
