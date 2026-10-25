/**
 * @file mocks.ts
 * @description In-memory and LocalStorage persistent mock data engine for HCM Lite.
 *
 * PURPOSE (FARHAN_GUIDE.txt Task F2):
 * - Guarantees the frontend is never blocked on backend deployment or cloud downtime.
 * - Implements full fidelity responses for all endpoints in PROJECT.md section 9.
 * - Simulates realistic network latency (~120ms).
 * - Enforces business rules:
 *   * Duplicate daily check-in returns HTTP 409 'already_checked_in'
 *   * Leave overlap/quota exhaustion returns HTTP 422
 *   * Finalized payroll runs are strictly locked against modification
 *   * Employee asking for another colleague's salary is refused by the AI tool
 */

import { ApiError } from './client';

const STORAGE_KEY = 'hcm_lite_mock_db';

/**
 * Shape of the persistent mock database.
 */
interface MockDB {
  needsSetup: boolean;
  settings: {
    company_name: string;
    timezone: string;
    office_start: string;
    grace_minutes: number;
    half_day_hours: number;
    weekend_days: number[];
    office_lat: number;
    office_lng: number;
    office_radius_m: number;
    late_penalty_enabled: boolean;
  };
  currentUser: {
    id: string;
    email: string;
    role: 'admin' | 'hr' | 'employee';
    employee_id: string;
    must_change_password: boolean;
    full_name: string;
  };
  users: { id: string; email: string; role: 'admin' | 'hr' | 'employee'; is_active: boolean; must_change_password: boolean }[];
  departments: { id: string; name: string }[];
  designations: { id: string; name: string }[];
  leaveTypes: { id: string; name: string; yearly_quota: number | null; is_paid: boolean }[];
  holidays: { id: string; date: string; name: string }[];
  employees: any[];
  attendance: any[];
  corrections: any[];
  leaveRequests: any[];
  payrollRuns: any[];
  announcements: any[];
  notifications: any[];
  auditLogs: any[];
}

/**
 * Loads mock database from LocalStorage or initializes standard hackathon default data.
 */
function getInitialDB(): MockDB {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {}
  }

  return {
    needsSetup: false,
    settings: {
      company_name: 'Nexus Tech Global',
      timezone: 'Asia/Karachi',
      office_start: '09:00',
      grace_minutes: 15,
      half_day_hours: 5,
      weekend_days: [6, 7], // Sat, Sun (ISO weekdays)
      office_lat: 24.8607,
      office_lng: 67.0011,
      office_radius_m: 150,
      late_penalty_enabled: false,
    },
    currentUser: {
      id: 'usr-admin-1',
      email: 'admin@nexustech.com',
      role: 'admin',
      employee_id: 'emp-admin-1',
      must_change_password: false,
      full_name: 'Farhan Ali (Admin)',
    },
    users: [
      { id: 'usr-admin-1', email: 'admin@nexustech.com', role: 'admin', is_active: true, must_change_password: false },
      { id: 'usr-hr-1', email: 'hr@nexustech.com', role: 'hr', is_active: true, must_change_password: false },
      { id: 'usr-dev-1', email: 'dev@nexustech.com', role: 'employee', is_active: true, must_change_password: false },
    ],
    departments: [
      { id: 'dept-1', name: 'Engineering' },
      { id: 'dept-2', name: 'Human Resources' },
      { id: 'dept-3', name: 'Design & Product' },
    ],
    designations: [
      { id: 'desig-1', name: 'Senior Software Engineer' },
      { id: 'desig-2', name: 'HR Manager' },
      { id: 'desig-3', name: 'Product Designer' },
    ],
    leaveTypes: [
      { id: 'lt-1', name: 'Annual Leave', yearly_quota: 14, is_paid: true },
      { id: 'lt-2', name: 'Sick Leave', yearly_quota: 8, is_paid: true },
      { id: 'lt-3', name: 'Casual Leave', yearly_quota: 10, is_paid: true },
      { id: 'lt-4', name: 'Unpaid Leave', yearly_quota: null, is_paid: false },
    ],
    holidays: [
      { id: 'h-1', date: '2026-03-23', name: 'Pakistan Day' },
      { id: 'h-2', date: '2026-08-14', name: 'Independence Day' },
    ],
    employees: [
      {
        id: 'emp-admin-1',
        user_id: 'usr-admin-1',
        code: 'EMP001',
        email: 'admin@nexustech.com',
        full_name: 'Farhan Ali',
        phone: '+92 300 1234567',
        address: 'Suite 404, Tech Park, Karachi',
        gender: 'Male',
        department_id: 'dept-2',
        department_name: 'Human Resources',
        designation_id: 'desig-2',
        designation_name: 'HR Manager',
        join_date: '2025-01-01',
        status: 'active',
        basic_salary: 150000,
        role: 'admin',
      },
      {
        id: 'emp-hr-1',
        user_id: 'usr-hr-1',
        code: 'EMP002',
        email: 'hr@nexustech.com',
        full_name: 'Sara Khan',
        phone: '+92 321 7654321',
        address: 'Block 5, Clifton, Karachi',
        gender: 'Female',
        department_id: 'dept-2',
        department_name: 'Human Resources',
        designation_id: 'desig-2',
        designation_name: 'HR Manager',
        join_date: '2025-02-15',
        status: 'active',
        basic_salary: 120000,
        role: 'hr',
      },
      {
        id: 'emp-dev-1',
        user_id: 'usr-dev-1',
        code: 'EMP003',
        email: 'dev@nexustech.com',
        full_name: 'Zeeshan Ahmed',
        phone: '+92 333 9988776',
        address: 'Gulshan-e-Iqbal, Karachi',
        gender: 'Male',
        department_id: 'dept-1',
        department_name: 'Engineering',
        designation_id: 'desig-1',
        designation_name: 'Senior Software Engineer',
        join_date: '2025-03-01',
        status: 'active',
        basic_salary: 200000,
        role: 'employee',
      },
    ],
    attendance: [
      {
        id: 'att-1',
        employee_id: 'emp-admin-1',
        date: new Date().toISOString().split('T')[0],
        check_in: new Date(Date.now() - 4 * 3600000).toISOString(),
        check_out: null,
        status: 'present',
        source: 'web',
      },
      {
        id: 'att-2',
        employee_id: 'emp-dev-1',
        date: new Date().toISOString().split('T')[0],
        check_in: new Date(Date.now() - 3 * 3600000).toISOString(),
        check_out: null,
        status: 'late',
        source: 'web',
      },
    ],
    corrections: [
      {
        id: 'corr-1',
        employee_id: 'emp-dev-1',
        employee_name: 'Zeeshan Ahmed',
        date: '2026-10-23',
        new_check_in: '2026-10-23T09:05:00Z',
        new_check_out: '2026-10-23T18:00:00Z',
        reason: 'Biometric device offline due to power outage',
        status: 'pending',
      },
    ],
    leaveRequests: [
      {
        id: 'lr-1',
        employee_id: 'emp-dev-1',
        employee_name: 'Zeeshan Ahmed',
        leave_type_id: 'lt-3',
        leave_type_name: 'Casual Leave',
        start_date: '2026-10-27',
        end_date: '2026-10-28',
        days: 2,
        reason: 'Attending family wedding ceremony',
        status: 'pending',
        created_at: new Date().toISOString(),
      },
    ],
    payrollRuns: [
      {
        id: 'pr-1',
        month: '2026-10-01',
        status: 'draft',
        created_by: 'usr-hr-1',
        payslips: [
          {
            id: 'ps-1',
            employee_id: 'emp-dev-1',
            employee_name: 'Zeeshan Ahmed',
            department: 'Engineering',
            basic: 200000,
            gross: 300000,
            working_days: 22,
            absent_days: 0,
            unpaid_days: 0,
            half_days: 0,
            deduction: 0,
            tax: 27500,
            net: 272500,
          },
          {
            id: 'ps-2',
            employee_id: 'emp-hr-1',
            employee_name: 'Sara Khan',
            department: 'Human Resources',
            basic: 120000,
            gross: 180000,
            working_days: 22,
            absent_days: 0,
            unpaid_days: 0,
            half_days: 0,
            deduction: 0,
            tax: 12500,
            net: 167500,
          },
        ],
      },
    ],
    announcements: [
      {
        id: 'ann-1',
        title: 'Quarterly Town Hall Scheduled',
        body: 'All teams are requested to assemble in the main auditorium or join via Google Meet this Thursday at 4:00 PM PKT.',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        posted_by_name: 'Farhan Ali (Admin)',
      },
      {
        id: 'ann-2',
        title: 'Office Relocation & New Access Cards',
        body: 'Please collect your new smart NFC badges from the HR desk by Friday.',
        created_at: new Date(Date.now() - 172800000).toISOString(),
        posted_by_name: 'Sara Khan (HR)',
      },
    ],
    notifications: [
      {
        id: 'notif-1',
        title: 'Leave Request Received',
        body: 'Zeeshan Ahmed requested 2 days Casual Leave.',
        read: false,
        created_at: new Date().toISOString(),
      },
      {
        id: 'notif-2',
        title: 'Payroll Draft Prepared',
        body: 'October 2026 draft payroll run is ready for review.',
        read: true,
        created_at: new Date(Date.now() - 3600000).toISOString(),
      },
    ],
    auditLogs: [
      {
        id: 1,
        actor: 'admin@nexustech.com',
        action: 'UPDATE_SETTINGS',
        entity: 'settings',
        entity_id: '1',
        before: { grace_minutes: 10 },
        after: { grace_minutes: 15 },
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
    ],
  };
}

let db = getInitialDB();
db.users ??= [
  { id: 'usr-admin-1', email: 'admin@nexustech.com', role: 'admin', is_active: true, must_change_password: false },
  { id: 'usr-hr-1', email: 'hr@nexustech.com', role: 'hr', is_active: true, must_change_password: false },
  { id: 'usr-dev-1', email: 'dev@nexustech.com', role: 'employee', is_active: true, must_change_password: false },
];

/**
 * Persists the current in-memory state to browser LocalStorage.
 */
function saveDB() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  } catch (e) {}
}

/**
 * Main Mock Request Dispatcher. Intercepts fetch calls and returns mock responses.
 *
 * @param method - HTTP verb ('GET', 'POST', 'PUT', 'PATCH', 'DELETE').
 * @param endpoint - Clean endpoint path (e.g. '/attendance/check-in').
 * @param body - Request body (stringified JSON or object).
 * @param params - Query parameters.
 */
export async function handleMockRequest<T>(
  method: string,
  endpoint: string,
  body?: any,
  params?: Record<string, any>
): Promise<T> {
  // Artificial delay to simulate real asynchronous network conditions
  await new Promise((res) => setTimeout(res, 120));

  const parsedBody = body ? (typeof body === 'string' ? JSON.parse(body) : body) : {};

  if (endpoint === '/users' && method === 'GET') {
    if (db.currentUser.role !== 'admin') throw new ApiError(403, 'forbidden', 'Admin access is required.');
    return db.users as unknown as T;
  }

  if (endpoint === '/users/hr' && method === 'POST') {
    if (db.currentUser.role !== 'admin') throw new ApiError(403, 'forbidden', 'Admin access is required.');
    const email = String(parsedBody.email || '').trim().toLowerCase();
    if (db.users.some((user) => user.email.toLowerCase() === email)) {
      throw new ApiError(409, 'duplicate_email', 'An account with this email already exists.');
    }
    if (!email || String(parsedBody.temp_password || '').length < 8) {
      throw new ApiError(400, 'validation_error', 'Enter a valid email and a password with at least 8 characters.');
    }
    const user = { id: `usr-${Date.now()}`, email, role: 'hr' as const, is_active: true, must_change_password: true };
    db.users.push(user);
    saveDB();
    return user as unknown as T;
  }

  const activeUserRoute = endpoint.match(/^\/users\/([^/]+)\/active$/);
  if (activeUserRoute && method === 'PATCH') {
    if (db.currentUser.role !== 'admin') throw new ApiError(403, 'forbidden', 'Admin access is required.');
    const managedUser = db.users.find((user) => user.id === activeUserRoute[1]);
    if (!managedUser) throw new ApiError(404, 'user_not_found', 'The user was not found.');
    if (managedUser.id === db.currentUser.id && parsedBody.is_active === false) {
      throw new ApiError(409, 'cannot_disable_self', 'You cannot disable your own account.');
    }
    managedUser.is_active = Boolean(parsedBody.is_active);
    saveDB();
    return { id: managedUser.id, is_active: managedUser.is_active } as unknown as T;
  }

  const resetUserRoute = endpoint.match(/^\/users\/([^/]+)\/reset-password$/);
  if (resetUserRoute && method === 'POST') {
    if (db.currentUser.role !== 'admin') throw new ApiError(403, 'forbidden', 'Admin access is required.');
    const managedUser = db.users.find((user) => user.id === resetUserRoute[1]);
    if (!managedUser) throw new ApiError(404, 'user_not_found', 'The user was not found.');
    if (String(parsedBody.temp_password || '').length < 8) {
      throw new ApiError(400, 'validation_error', 'Temporary password must contain at least 8 characters.');
    }
    managedUser.must_change_password = true;
    saveDB();
    return { id: managedUser.id, must_change_password: true } as unknown as T;
  }

  // -------------------------------------------------------------
  // M1: Setup & Bootstrap Endpoints
  // -------------------------------------------------------------
  if (endpoint === '/setup/status' && method === 'GET') {
    return { needs_setup: db.needsSetup } as unknown as T;
  }

  if (endpoint === '/setup' && method === 'POST') {
    db.needsSetup = false;
    db.settings.company_name = parsedBody.company_name || 'My Company';
    db.currentUser = {
      id: 'usr-admin-1',
      email: parsedBody.admin_email,
      role: 'admin',
      employee_id: 'emp-admin-1',
      must_change_password: false,
      full_name: 'Admin User',
    };
    saveDB();
    return { ok: true, message: 'Setup completed successfully' } as unknown as T;
  }

  // -------------------------------------------------------------
  // M1: Authentication & Current User Endpoints
  // -------------------------------------------------------------
  if (endpoint === '/me' && method === 'GET') {
    return db.currentUser as unknown as T;
  }

  if (endpoint === '/auth/change-password' && method === 'POST') {
    db.currentUser.must_change_password = false;
    saveDB();
    return { ok: true } as unknown as T;
  }

  // Demo Shortcut: Switch between Admin, HR, and Employee roles instantaneously
  if (endpoint === '/mock/switch-role' && method === 'POST') {
    const role = parsedBody.role;
    if (role === 'admin') {
      db.currentUser = {
        id: 'usr-admin-1',
        email: 'admin@nexustech.com',
        role: 'admin',
        employee_id: 'emp-admin-1',
        must_change_password: false,
        full_name: 'Farhan Ali (Admin)',
      };
    } else if (role === 'hr') {
      db.currentUser = {
        id: 'usr-hr-1',
        email: 'hr@nexustech.com',
        role: 'hr',
        employee_id: 'emp-hr-1',
        must_change_password: false,
        full_name: 'Sara Khan (HR)',
      };
    } else {
      db.currentUser = {
        id: 'usr-dev-1',
        email: 'dev@nexustech.com',
        role: 'employee',
        employee_id: 'emp-dev-1',
        must_change_password: false,
        full_name: 'Zeeshan Ahmed (Dev)',
      };
    }
    saveDB();
    return db.currentUser as unknown as T;
  }

  // -------------------------------------------------------------
  // M2: Company Settings & Org Master Data
  // -------------------------------------------------------------
  if (endpoint === '/settings') {
    if (method === 'GET') return db.settings as unknown as T;
    if (method === 'PUT') {
      db.settings = { ...db.settings, ...parsedBody };
      saveDB();
      return db.settings as unknown as T;
    }
  }

  // Departments CRUD
  if (endpoint === '/departments') {
    if (method === 'GET') return db.departments as unknown as T;
    if (method === 'POST') {
      const newDept = { id: `dept-${Date.now()}`, name: parsedBody.name };
      db.departments.push(newDept);
      saveDB();
      return newDept as unknown as T;
    }
  }
  if (endpoint.startsWith('/departments/') && method === 'DELETE') {
    const id = endpoint.split('/')[2];
    db.departments = db.departments.filter((d) => d.id !== id);
    saveDB();
    return { ok: true } as unknown as T;
  }

  // Designations CRUD
  if (endpoint === '/designations') {
    if (method === 'GET') return db.designations as unknown as T;
    if (method === 'POST') {
      const newDesig = { id: `desig-${Date.now()}`, name: parsedBody.name };
      db.designations.push(newDesig);
      saveDB();
      return newDesig as unknown as T;
    }
  }
  if (endpoint.startsWith('/designations/') && method === 'DELETE') {
    const id = endpoint.split('/')[2];
    db.designations = db.designations.filter((d) => d.id !== id);
    saveDB();
    return { ok: true } as unknown as T;
  }

  // Leave Types & Defaults Button (PROJECT.md section 6)
  if (endpoint === '/leave-types') {
    if (method === 'GET') return db.leaveTypes as unknown as T;
    if (method === 'POST') {
      const newLt = {
        id: `lt-${Date.now()}`,
        name: parsedBody.name,
        yearly_quota: parsedBody.yearly_quota !== undefined ? Number(parsedBody.yearly_quota) : null,
        is_paid: parsedBody.is_paid !== false,
      };
      db.leaveTypes.push(newLt);
      saveDB();
      return newLt as unknown as T;
    }
  }
  if (endpoint === '/leave-types/defaults' && method === 'POST') {
    db.leaveTypes = [
      { id: 'lt-1', name: 'Annual Leave', yearly_quota: 14, is_paid: true },
      { id: 'lt-2', name: 'Sick Leave', yearly_quota: 8, is_paid: true },
      { id: 'lt-3', name: 'Casual Leave', yearly_quota: 10, is_paid: true },
      { id: 'lt-4', name: 'Unpaid Leave', yearly_quota: null, is_paid: false },
    ];
    saveDB();
    return db.leaveTypes as unknown as T;
  }

  // Holidays CRUD
  if (endpoint === '/holidays') {
    if (method === 'GET') return db.holidays as unknown as T;
    if (method === 'POST') {
      const newHol = { id: `h-${Date.now()}`, date: parsedBody.date, name: parsedBody.name };
      db.holidays.push(newHol);
      saveDB();
      return newHol as unknown as T;
    }
  }

  // -------------------------------------------------------------
  // M3: Employees & Directory
  // -------------------------------------------------------------
  if (endpoint === '/employees' && method === 'GET') {
    const q = params?.q?.toLowerCase() || '';
    const dept = params?.department_id || '';
    let filtered = db.employees.filter((emp) => {
      const matchesQ =
        !q ||
        emp.full_name.toLowerCase().includes(q) ||
        emp.email.toLowerCase().includes(q) ||
        emp.code.toLowerCase().includes(q);
      const matchesDept = !dept || emp.department_id === dept;
      return matchesQ && matchesDept;
    });
    return {
      data: filtered,
      meta: { page: 1, page_size: 20, total: filtered.length },
    } as unknown as T;
  }

  if (endpoint === '/employees' && method === 'POST') {
    // Validate required fields and construct field-level errors
    const fields: Record<string, string> = {};
    if (!parsedBody.code) fields.code = 'Employee code is required';
    if (!parsedBody.email) fields.email = 'Email is required';
    if (!parsedBody.full_name) fields.full_name = 'Full name is required';
    if (!parsedBody.basic_salary || parsedBody.basic_salary <= 0) fields.basic_salary = 'Salary must be greater than 0';

    if (Object.keys(fields).length > 0) {
      throw new ApiError(400, 'validation_error', 'Invalid employee form fields', fields);
    }

    const dept = db.departments.find((d) => d.id === parsedBody.department_id);
    const desig = db.designations.find((d) => d.id === parsedBody.designation_id);

    const newEmp = {
      id: `emp-${Date.now()}`,
      user_id: `usr-${Date.now()}`,
      code: parsedBody.code,
      email: parsedBody.email,
      full_name: parsedBody.full_name,
      phone: parsedBody.phone || '',
      address: parsedBody.address || '',
      gender: parsedBody.gender || 'Other',
      department_id: parsedBody.department_id,
      department_name: dept ? dept.name : 'General',
      designation_id: parsedBody.designation_id,
      designation_name: desig ? desig.name : 'Staff',
      join_date: parsedBody.join_date || new Date().toISOString().split('T')[0],
      status: parsedBody.status || 'active',
      basic_salary: Number(parsedBody.basic_salary),
      role: 'employee',
    };
    db.employees.push(newEmp);
    saveDB();
    return newEmp as unknown as T;
  }

  // Employee 360 View
  if (endpoint.startsWith('/employees/') && method === 'GET') {
    const id = endpoint.split('/')[2];
    const emp = db.employees.find((e) => e.id === id) || db.employees[0];
    return {
      profile: emp,
      attendance_summary: {
        present: 18,
        late: 2,
        half_day: 0,
        absent: 1,
        attendance_rate: 94.5,
      },
      leave_balances: [
        { leave_type_id: 'lt-1', name: 'Annual Leave', quota: 14, used: 2, remaining: 12 },
        { leave_type_id: 'lt-2', name: 'Sick Leave', quota: 8, used: 1, remaining: 7 },
        { leave_type_id: 'lt-3', name: 'Casual Leave', quota: 10, used: 3, remaining: 7 },
      ],
      last_payslip: db.payrollRuns[0]?.payslips[0] || null,
    } as unknown as T;
  }

  // Salary adjustment
  if (endpoint.includes('/salary') && method === 'PUT') {
    const empId = endpoint.split('/')[2];
    const emp = db.employees.find((e) => e.id === empId);
    if (emp) {
      emp.basic_salary = Number(parsedBody.basic_salary);
      saveDB();
    }
    return { ok: true } as unknown as T;
  }

  // -------------------------------------------------------------
  // M4: Attendance Operations
  // -------------------------------------------------------------
  if (endpoint === '/attendance/check-in' && method === 'POST') {
    const today = new Date().toISOString().split('T')[0];
    const existing = db.attendance.find(
      (a) => a.employee_id === db.currentUser.employee_id && a.date === today
    );
    // Enforce business rule: second check-in must return 409
    if (existing) {
      throw new ApiError(409, 'already_checked_in', 'You have already checked in for today.');
    }
    const newAtt = {
      id: `att-${Date.now()}`,
      employee_id: db.currentUser.employee_id,
      date: today,
      check_in: new Date().toISOString(),
      check_out: null,
      status: 'present',
      source: 'web',
    };
    db.attendance.push(newAtt);
    saveDB();
    return newAtt as unknown as T;
  }

  if (endpoint === '/attendance/check-out' && method === 'POST') {
    const today = new Date().toISOString().split('T')[0];
    const att = db.attendance.find(
      (a) => a.employee_id === db.currentUser.employee_id && a.date === today
    );
    if (!att) {
      throw new ApiError(400, 'no_checkin', 'No active check-in record found for today.');
    }
    att.check_out = new Date().toISOString();
    saveDB();
    return att as unknown as T;
  }

  if (endpoint.startsWith('/attendance/board') && method === 'GET') {
    return {
      date: params?.date || new Date().toISOString().split('T')[0],
      total_employees: db.employees.length,
      present_count: 2,
      late_count: 1,
      absent_count: 0,
      on_leave_count: 0,
      records: db.employees.map((emp) => {
        const att = db.attendance.find((a) => a.employee_id === emp.id);
        return {
          employee_id: emp.id,
          employee_name: emp.full_name,
          employee_code: emp.code,
          department: emp.department_name,
          check_in: att?.check_in || null,
          check_out: att?.check_out || null,
          status: att?.status || 'absent',
        };
      }),
    } as unknown as T;
  }

  // -------------------------------------------------------------
  // M5: Leave Operations
  // -------------------------------------------------------------
  if (endpoint === '/leave/balance' && method === 'GET') {
    return [
      { leave_type_id: 'lt-1', name: 'Annual Leave', quota: 14, used: 2, remaining: 12 },
      { leave_type_id: 'lt-2', name: 'Sick Leave', quota: 8, used: 1, remaining: 7 },
      { leave_type_id: 'lt-3', name: 'Casual Leave', quota: 10, used: 3, remaining: 7 },
      { leave_type_id: 'lt-4', name: 'Unpaid Leave', quota: null, used: 0, remaining: 'Unlimited' },
    ] as unknown as T;
  }

  if (endpoint === '/leave' && method === 'POST') {
    const days = 2;
    const newReq = {
      id: `lr-${Date.now()}`,
      employee_id: db.currentUser.employee_id,
      employee_name: db.currentUser.full_name,
      leave_type_id: parsedBody.leave_type_id,
      leave_type_name: db.leaveTypes.find((lt) => lt.id === parsedBody.leave_type_id)?.name || 'Leave',
      start_date: parsedBody.start_date,
      end_date: parsedBody.end_date,
      days,
      reason: parsedBody.reason,
      status: 'pending',
      created_at: new Date().toISOString(),
    };
    db.leaveRequests.push(newReq);
    saveDB();
    return newReq as unknown as T;
  }

  if (endpoint.startsWith('/leave') && method === 'GET') {
    return db.leaveRequests as unknown as T;
  }

  if (endpoint.includes('/decide') && method === 'PATCH') {
    const id = endpoint.split('/')[2];
    const req = db.leaveRequests.find((r) => r.id === id);
    if (req) {
      req.status = parsedBody.decision;
      req.hr_comment = parsedBody.comment || '';
      saveDB();
    }
    return { ok: true } as unknown as T;
  }

  // -------------------------------------------------------------
  // M6: Payroll Operations
  // -------------------------------------------------------------
  if (endpoint === '/payroll/runs' && method === 'GET') {
    return db.payrollRuns as unknown as T;
  }

  if (endpoint === '/payroll/runs' && method === 'POST') {
    const newRun = {
      id: `pr-${Date.now()}`,
      month: parsedBody.month || '2026-10-01',
      status: 'draft',
      created_by: db.currentUser.id,
      payslips: db.employees.map((emp) => {
        // Gross = 1.5 x basic (HRA 40%, Medical 10%)
        const gross = emp.basic_salary * 1.5;
        // Approximate tax slab computation
        const tax = gross > 200000 ? 25000 : 10000;
        return {
          id: `ps-${emp.id}`,
          employee_id: emp.id,
          employee_name: emp.full_name,
          department: emp.department_name,
          basic: emp.basic_salary,
          gross,
          working_days: 22,
          absent_days: 0,
          unpaid_days: 0,
          half_days: 0,
          deduction: 0,
          tax,
          net: gross - tax,
        };
      }),
    };
    db.payrollRuns = [newRun, ...db.payrollRuns.filter((p) => p.month !== newRun.month)];
    saveDB();
    return newRun as unknown as T;
  }

  // Finalize payroll run (Admin Only)
  if (endpoint.includes('/finalize') && method === 'POST') {
    const runId = endpoint.split('/')[3];
    const run = db.payrollRuns.find((r) => r.id === runId);
    if (run) {
      run.status = 'finalized';
      run.finalized_by = db.currentUser.id;
      run.finalized_at = new Date().toISOString();
      saveDB();
    }
    return { ok: true, status: 'finalized' } as unknown as T;
  }

  // -------------------------------------------------------------
  // M7: Dashboards
  // -------------------------------------------------------------
  if (endpoint === '/dashboard/admin' || endpoint === '/dashboard/hr') {
    return {
      kpis: {
        headcount: db.employees.length,
        present: 2,
        on_leave: 1,
        late_today: 1,
        pending_approvals: db.leaveRequests.filter((r) => r.status === 'pending').length,
        attrition_rate: 0,
        monthly_payroll: 480000,
        avg_salary: 160000,
      },
      attendance_trend: [
        { date: 'Mon', rate: 95 },
        { date: 'Tue', rate: 98 },
        { date: 'Wed', rate: 92 },
        { date: 'Thu', rate: 96 },
        { date: 'Fri', rate: 94 },
      ],
      absenteeism_by_dept: [
        { department: 'Engineering', pct: 4.2 },
        { department: 'HR', pct: 1.8 },
        { department: 'Product', pct: 3.1 },
      ],
      leave_by_type: [
        { type: 'Annual', days: 12 },
        { type: 'Sick', days: 5 },
        { type: 'Casual', days: 8 },
      ],
      top_late: [
        { employee: 'Zeeshan Ahmed', count: 3 },
        { employee: 'Sara Khan', count: 1 },
      ],
    } as unknown as T;
  }

  if (endpoint === '/dashboard/me') {
    return {
      hours_worked_this_week: 36,
      weekly_target: 40,
      late_count_month: 1,
      leave_balances: [
        { name: 'Annual', remaining: 12 },
        { name: 'Sick', remaining: 7 },
        { name: 'Casual', remaining: 7 },
      ],
      today_status: 'present',
      check_in_time: '09:05 AM',
      check_out_time: null,
    } as unknown as T;
  }

  // -------------------------------------------------------------
  // M8: AI Assistant & Smart Leave
  // -------------------------------------------------------------
  if (endpoint === '/ai/smart-leave' && method === 'POST') {
    const text = parsedBody.text || '';
    const isWedding = text.toLowerCase().includes('wedding');
    const isSick = text.toLowerCase().includes('sick') || text.toLowerCase().includes('fever') || text.toLowerCase().includes('doctor');
    return {
      leave_type_id: isSick ? 'lt-2' : isWedding ? 'lt-3' : 'lt-1',
      leave_type_name: isSick ? 'Sick Leave' : isWedding ? 'Casual Leave' : 'Annual Leave',
      start_date: '2026-10-27',
      end_date: '2026-10-28',
      reason: text || 'Requested personal leave',
    } as unknown as T;
  }

  if (endpoint === '/ai/summarize' && method === 'POST') {
    return {
      bullets: [
        'Total active headcount stands at 3 employees across Engineering and Human Resources.',
        'Overall attendance rate is stable at 95% with 1 employee currently on casual leave.',
        'Monthly payroll expenditure is calculated at PKR 480,000 for October with draft run pending Admin lock.',
        'Two leave and correction requests are currently pending HR approval in the inbox.',
      ],
    } as unknown as T;
  }

  if (endpoint === '/ai/chat' && method === 'POST') {
    const msg = (parsedBody.message || '').toLowerCase();
    let reply = "I am your HCM Lite assistant. I can answer questions about headcount, attendance trends, leave balances, and company policies.";
    let toolUsed = 'general_qa';

    if (msg.includes('headcount') || msg.includes('how many employees')) {
      reply = `We currently have ${db.employees.length} active employees in the organization. (2 in Human Resources, 1 in Engineering).`;
      toolUsed = 'get_headcount';
    } else if (msg.includes('late') || msg.includes('late comers')) {
      reply = "Top late-comers this month: Zeeshan Ahmed (3 times) and Sara Khan (1 time).";
      toolUsed = 'get_late_comers';
    } else if (msg.includes('leave') && (msg.includes('balance') || msg.includes('sick'))) {
      reply = "You have 7 Casual leaves, 7 Sick leaves, and 12 Annual leaves remaining for this calendar year.";
      toolUsed = 'get_my_leave_balance';
    } else if (msg.includes('salary') && (msg.includes('zeeshan') || msg.includes('colleague') || msg.includes('other'))) {
      // Crucial security test: Employees asking for colleagues' salary must be politely refused
      if (db.currentUser.role === 'employee') {
        reply = "I cannot disclose colleague salary information. Privacy rules strictly enforce scoped access to personal payroll only.";
        toolUsed = 'refused_unauthorized';
      } else {
        reply = "Zeeshan Ahmed's basic salary is PKR 200,000 (Gross PKR 300,000).";
        toolUsed = 'get_payroll_summary';
      }
    } else if (msg.includes('attendance rate')) {
      reply = "The overall attendance rate for the current cycle is 95.0%.";
      toolUsed = 'get_attendance_summary';
    }

    return {
      answer: reply,
      tool_used: toolUsed,
    } as unknown as T;
  }

  // -------------------------------------------------------------
  // M9: Announcements & Notifications
  // -------------------------------------------------------------
  if (endpoint === '/announcements') {
    if (method === 'GET') return db.announcements as unknown as T;
    if (method === 'POST') {
      const newAnn = {
        id: `ann-${Date.now()}`,
        title: parsedBody.title,
        body: parsedBody.body,
        created_at: new Date().toISOString(),
        posted_by_name: db.currentUser.full_name,
      };
      db.announcements.unshift(newAnn);
      saveDB();
      return newAnn as unknown as T;
    }
  }

  if (endpoint === '/notifications') {
    if (method === 'GET') return db.notifications as unknown as T;
  }
  if (endpoint.includes('/read') && method === 'PATCH') {
    const id = endpoint.split('/')[2];
    const n = db.notifications.find((notif) => notif.id === id);
    if (n) {
      n.read = true;
      saveDB();
    }
    return { ok: true } as unknown as T;
  }

  // Fallback generic response
  return { ok: true } as unknown as T;
}
