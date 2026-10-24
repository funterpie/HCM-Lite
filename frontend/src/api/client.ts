import { supabase } from '@/lib/supabase';
import { handleMockRequest } from './mocks';

export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string>;

  constructor(status: number, code: string, message: string, fields?: Record<string, string>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method || 'GET';
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Handle Mock Mode
  if (USE_MOCKS) {
    try {
      const mockResult = await handleMockRequest<T>(method, cleanEndpoint, options.body, options.params);
      return mockResult;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(500, 'mock_error', (err as Error).message);
    }
  }

  // Real API Mode with Bearer Token from Supabase
  let token: string | undefined;
  try {
    const { data } = await supabase.auth.getSession();
    token = data.session?.access_token;
  } catch (e) {
    // Ignore if session retrieval fails in offline/mock
  }

  const url = new URL(`${BASE_URL}${cleanEndpoint}`);
  if (options.params) {
    Object.entries(options.params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        url.searchParams.append(key, String(val));
      }
    });
  }

  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(url.toString(), {
    ...options,
    headers,
  });

  // Handle special blob response for PDF download
  if (endpoint.includes('/pdf')) {
    if (!res.ok) {
      throw new ApiError(res.status, 'download_failed', 'Failed to download PDF');
    }
    return (await res.blob()) as unknown as T;
  }

  const json = await res.json().catch(() => ({}));

  if (!res.ok || json.error) {
    const err = json.error || {};
    throw new ApiError(
      res.status,
      err.code || 'unknown_error',
      err.message || 'An error occurred',
      err.fields
    );
  }

  // If response has meta (for paginated lists), return full object; otherwise unwrap data
  if (json.meta) {
    return json as T;
  }
  return json.data !== undefined ? json.data : json;
}

export const api = {
  get: <T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>) =>
    request<T>(endpoint, { method: 'GET', params }),
  post: <T>(endpoint: string, body?: any, params?: Record<string, string | number | boolean | undefined>) =>
    request<T>(endpoint, { method: 'POST', body: body ? JSON.stringify(body) : undefined, params }),
  put: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),
};
