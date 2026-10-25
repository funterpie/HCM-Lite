/**
 * @file client.ts
 * @description Centralized HTTP API client with Bearer token injection, error envelope handling,
 * and support for an offline mock data engine (`VITE_USE_MOCKS=true`).
 *
 * CONTRACT COMPLIANCE (PROJECT.md section 9):
 * - Base path: `/api`
 * - JSON responses: `{ "data": ... }` or `{ "data": [...], "meta": { "page", "page_size", "total" } }`
 * - Standard Error Envelope: `{ "error": { "code": "string", "message": "string", "fields": { ... } } }`
 * - Throws typed `ApiError` instances exposing HTTP status, error code, and field-level validation errors.
 */

import { supabase } from '@/lib/supabase';
import { handleMockRequest } from './mocks';

/**
 * Standard typed error representing an API contract failure or validation rejection.
 */
export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string>;

  /**
   * @param status - HTTP response status code (e.g., 400, 401, 403, 409, 422).
   * @param code - Application error code (e.g. 'already_checked_in', 'overlap', 'validation_error').
   * @param message - User-friendly error message.
   * @param fields - Optional map of field names to specific validation error messages.
   */
  constructor(status: number, code: string, message: string, fields?: Record<string, string>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

// Configuration from environment variables
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

interface RequestOptions extends RequestInit {
  /** Optional query parameters appended to the URL */
  params?: Record<string, string | number | boolean | undefined>;
}

/**
 * Core internal HTTP request executor.
 * Handles token attachment, response parsing, error envelope unwrapping, and mock interception.
 */
async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method || 'GET';
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // 1. Intercept call if Mock Engine is enabled (allows zero-dependency frontend testing)
  if (USE_MOCKS) {
    try {
      const mockResult = await handleMockRequest<T>(method, cleanEndpoint, options.body, options.params);
      return mockResult;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(500, 'mock_error', (err as Error).message);
    }
  }

  // 2. Real API Mode: Fetch JWT access token from Supabase Auth session
  let token: string | undefined;
  try {
    const { data } = await supabase.auth.getSession();
    token = data.session?.access_token;
  } catch (e) {
    // Session retrieval skipped in unauthenticated or offline scenarios
  }

  // 3. Construct URL with query parameters
  const url = new URL(`${BASE_URL}${cleanEndpoint}`);
  if (options.params) {
    Object.entries(options.params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        url.searchParams.append(key, String(val));
      }
    });
  }

  // 4. Inject Authorization and Content-Type headers
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(url.toString(), {
    ...options,
    headers,
  });

  // 5. Special handling for binary blob downloads (e.g. ReportLab Payslip PDF)
  if (endpoint.includes('/pdf')) {
    if (!res.ok) {
      throw new ApiError(res.status, 'download_failed', 'Failed to download PDF');
    }
    return (await res.blob()) as unknown as T;
  }

  // 6. Parse JSON payload
  const json = await res.json().catch(() => ({}));

  // 7. Unwrap and throw structured ApiError if the server returned an error envelope
  if (!res.ok || json.error) {
    const err = json.error || {};
    throw new ApiError(
      res.status,
      err.code || 'unknown_error',
      err.message || 'An error occurred',
      err.fields
    );
  }

  // 8. Handle Paginated Lists: return `{ data, meta }` if meta exists
  if (json.meta) {
    return json as T;
  }

  // 9. Standard Success: unwrap `{ data }` envelope
  return json.data !== undefined ? json.data : json;
}

/**
 * Public typed API client exposing standard REST methods.
 */
export const api = {
  /** Send GET request */
  get: <T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>) =>
    request<T>(endpoint, { method: 'GET', params }),

  /** Send POST request with JSON body */
  post: <T>(endpoint: string, body?: any, params?: Record<string, string | number | boolean | undefined>) =>
    request<T>(endpoint, { method: 'POST', body: body ? JSON.stringify(body) : undefined, params }),

  /** Send PUT request with JSON body */
  put: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),

  /** Send PATCH request with JSON body */
  patch: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),

  /** Send DELETE request */
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),
};
