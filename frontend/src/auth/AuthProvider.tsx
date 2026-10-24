import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '@/api/client';
import { supabase } from '@/lib/supabase';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export interface User {
  id: string;
  email: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id: string;
  must_change_password: boolean;
  full_name?: string;
}

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
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  const fetchStatusAndUser = async () => {
    try {
      setLoading(true);
      // Check setup status first
      try {
        const setupRes = await api.get<{ needs_setup: boolean }>('/setup/status');
        if (setupRes?.needs_setup) {
          setNeedsSetup(true);
          setLoading(false);
          return;
        }
      } catch (e) {
        // Continue
      }

      // Check current user
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

  const login = async (email: string, password: string) => {
    const isMock = import.meta.env.VITE_USE_MOCKS === 'true';
    if (!isMock) {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
    }
    await fetchStatusAndUser();
  };

  const logout = async () => {
    const isMock = import.meta.env.VITE_USE_MOCKS === 'true';
    if (!isMock) {
      await supabase.auth.signOut();
    }
    setUser(null);
  };

  const switchMockRole = async (role: 'admin' | 'hr' | 'employee') => {
    await api.post('/mock/switch-role', { role });
    await fetchStatusAndUser();
  };

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

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
