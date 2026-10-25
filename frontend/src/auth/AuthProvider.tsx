/**
 * @file AuthProvider.tsx
 * @description Authentication context, React Query provider, and session manager.
 *
 * AUTH RULES (PROJECT.md section 6 & FARHAN_GUIDE.txt Task F2, F3):
 * - Keeps user identity `{ id, email, role, employee_id, must_change_password }`.
 * - Validates first-run status on mount (`GET /setup/status`).
 * - Automatically forces the ChangePassword screen when `must_change_password === true`.
 * - Provides `switchMockRole` allowing judges/evaluators to seamlessly test Admin, HR, and Employee.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '@/api/client';
import { supabase } from '@/lib/supabase';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

/**
 * Shape of the authenticated user profile returned by `GET /me`.
 */
export interface User {
  id: string;
  email: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id: string;
  must_change_password: boolean;
  full_name?: string;
}

/**
 * Interface contract exposed by the Auth context.
 */
interface AuthContextType {
  user: User | null;
  loading: boolean;
  needsSetup: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchMockRole: (role: 'admin' | 'hr' | 'employee') => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Shared React Query client for background data caching and refetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * AuthProvider component that wraps the root application.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  /**
   * Checks organization bootstrap status and fetches current logged-in user profile.
   */
  const fetchStatusAndUser = async () => {
    try {
      setLoading(true);
      // 1. Verify if this is a fresh install requiring initial master setup
      try {
        const setupRes = await api.get<{ needs_setup: boolean }>('/setup/status');
        if (setupRes?.needs_setup) {
          setNeedsSetup(true);
          setLoading(false);
          return;
        }
      } catch (e) {
        // Continue if setup check is non-blocking
      }

      // 2. Fetch authenticated profile from FastAPI backend
      const userData = await api.get<User>('/me');
      setUser(userData);
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatusAndUser();
  }, []);

  /**
   * Authenticates user via Supabase Auth (or mock handler in mock mode).
   */
  const login = async (email: string, password: string) => {
    const isMock = import.meta.env.VITE_USE_MOCKS === 'true';
    if (!isMock) {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
    }
    await fetchStatusAndUser();
  };

  /**
   * Signs out current user session.
   */
  const logout = async () => {
    const isMock = import.meta.env.VITE_USE_MOCKS === 'true';
    if (!isMock) {
      await supabase.auth.signOut();
    }
    setUser(null);
  };

  /**
   * Quick role-switching utility for hackathon judges to evaluate all 3 roles instantly.
   */
  const switchMockRole = async (role: 'admin' | 'hr' | 'employee') => {
    await api.post('/mock/switch-role', { role });
    await fetchStatusAndUser();
  };

  /**
   * Re-evaluates current user session and profile flags (e.g. after password change).
   */
  const refreshUser = async () => {
    await fetchStatusAndUser();
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider
        value={{
          user,
          loading,
          needsSetup,
          login,
          logout,
          switchMockRole,
          refreshUser,
        }}
      >
        {children}
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

/**
 * Hook to consume the AuthContext within any child component.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
