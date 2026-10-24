-- HCM Lite schema. Run once in Supabase -> SQL editor on a fresh project.
-- No seed data on purpose: Admin creates everything through the app.

create extension if not exists "pgcrypto";

create type user_role      as enum ('admin','hr','employee');
create type att_status     as enum ('present','late','half_day','absent','missing_checkout','on_leave');
create type req_status     as enum ('pending','approved','rejected','cancelled');
create type payroll_status as enum ('draft','finalized');

-- single-row company settings (M2). Empty table = fresh install = /setup is allowed.
create table settings (
  id int primary key default 1 check (id = 1),
  company_name text not null,
  timezone text not null default 'Asia/Karachi',
  office_start time not null default '09:00',
  grace_minutes int not null default 15,
  half_day_hours numeric not null default 5,
  weekend_days int[] not null default '{6,7}',           -- ISO weekday: Mon=1 .. Sun=7 (Sat, Sun)
  office_lat double precision,
  office_lng double precision,
  office_radius_m int default 150,
  late_penalty_enabled boolean not null default false     -- bonus: 3 lates = 0.5 day
);

create table departments  (id uuid primary key default gen_random_uuid(), name text unique not null);
create table designations (id uuid primary key default gen_random_uuid(), name text unique not null);
create table leave_types  (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  yearly_quota int,                                       -- null = unlimited (unpaid)
  is_paid boolean not null default true
);
create table holidays (id uuid primary key default gen_random_uuid(), date date unique not null, name text not null);

-- one row per login; auth.users is owned by Supabase Auth
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role user_role not null,
  must_change_password boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table employees (
  id uuid primary key default gen_random_uuid(),
  user_id uuid unique references profiles(id),
  code text unique not null,
  email text unique not null,
  full_name text not null,
  phone text,
  address text,
  gender text,
  department_id uuid references departments(id),
  designation_id uuid references designations(id),
  join_date date not null,
  exit_date date,
  status text not null default 'active' check (status in ('active','probation','exited')),
  basic_salary numeric not null check (basic_salary > 0)  -- gross = 1.5 x basic
);
create index on employees (department_id);
create index on employees (status);

create table attendance (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references employees(id),
  date date not null,
  check_in timestamptz,
  check_out timestamptz,
  status att_status not null,
  source text not null default 'web',                     -- web | camera | correction
  unique (employee_id, date)                              -- second check-in => 409
);
create index on attendance (date);

create table attendance_corrections (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references employees(id),
  date date not null,
  new_check_in timestamptz,
  new_check_out timestamptz,
  reason text not null,
  status req_status not null default 'pending',
  hr_comment text,
  decided_by uuid references profiles(id),
  decided_at timestamptz
);

create table leave_requests (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references employees(id),
  leave_type_id uuid not null references leave_types(id),
  start_date date not null,
  end_date date not null,
  days int not null check (days > 0),                     -- working days only
  reason text,
  status req_status not null default 'pending',
  hr_comment text,
  decided_by uuid references profiles(id),
  decided_at timestamptz,
  created_at timestamptz not null default now(),
  check (end_date >= start_date)
);
create index on leave_requests (employee_id, status);

create table payroll_runs (
  id uuid primary key default gen_random_uuid(),
  month date not null unique,                             -- first day of the month
  status payroll_status not null default 'draft',
  created_by uuid references profiles(id),
  finalized_by uuid references profiles(id),
  finalized_at timestamptz
);

create table payslips (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references payroll_runs(id) on delete cascade,
  employee_id uuid not null references employees(id),
  basic numeric, gross numeric,
  working_days int,                                       -- payable window after proration
  absent_days numeric, unpaid_days numeric, half_days int,
  deduction numeric, tax numeric, net numeric,
  unique (run_id, employee_id)
);

create table announcements (
  id uuid primary key default gen_random_uuid(),
  title text not null, body text not null,
  posted_by uuid references profiles(id),
  created_at timestamptz not null default now()
);

create table notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id),
  title text not null, body text,
  read boolean not null default false,
  created_at timestamptz not null default now()
);
create index on notifications (user_id, read);

create table audit_logs (
  id bigserial primary key,
  actor_id uuid,
  action text not null,
  entity text not null,
  entity_id text,
  before jsonb, after jsonb,
  created_at timestamptz not null default now()
);

create table ai_logs (
  id bigserial primary key,
  user_id uuid,
  kind text,                                              -- chat | summary | smart_leave
  prompt text, tool text, response text,
  latency_ms int, ok boolean,
  created_at timestamptz not null default now()
);

-- Audit log is append-only
create rule audit_no_update as on update to audit_logs do instead nothing;
create rule audit_no_delete as on delete to audit_logs do instead nothing;

-- Finalized payroll is locked
create function lock_finalized_run() returns trigger language plpgsql as $$
begin
  if old.status = 'finalized' then raise exception 'payroll run is finalized'; end if;
  return coalesce(new, old);
end $$;
create trigger payroll_runs_lock before update or delete on payroll_runs
  for each row execute function lock_finalized_run();

create function lock_finalized_payslip() returns trigger language plpgsql as $$
begin
  if (select status from payroll_runs where id = old.run_id) = 'finalized' then
    raise exception 'payroll run is finalized';
  end if;
  return coalesce(new, old);
end $$;
create trigger payslips_lock before update or delete on payslips
  for each row execute function lock_finalized_payslip();

-- Deny-all for the public API (anon/authenticated keys). Only the backend's
-- service-role connection reads or writes data.
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table %I enable row level security', t);
  end loop;
end $$;
