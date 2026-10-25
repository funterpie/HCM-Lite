/**
 * @file Login.tsx
 * @description Authentication screen with 1-click test credential presets for quick hackathon judging.
 *
 * SPECIFICATION (FARHAN.md):
 * - Signs in via Supabase Auth `signInWithPassword`.
 * - Redirects to `/setup` if organization is not yet provisioned.
 * - Forces `/change-password` if profile flag `must_change_password === true`.
 * - Redirects authenticated users to their corresponding role dashboard (`/${role}/dashboard`).
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { ShieldCheck, LogIn } from 'lucide-react';

export function Login() {
  const { login, user, needsSetup, switchMockRole } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const isMock = import.meta.env.VITE_USE_MOCKS === 'true';
  const companyName = import.meta.env.VITE_COMPANY_NAME?.trim() || 'HCM Lite';

  // Automatically route according to account setup & password change flags
  React.useEffect(() => {
    if (needsSetup) {
      navigate('/setup');
    } else if (user) {
      if (user.must_change_password) {
        navigate('/change-password');
      } else {
        navigate(`/${user.role}/dashboard`);
      }
    }
  }, [user, needsSetup, navigate]);

  /**
   * Handles user submission of email and password credentials.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 1-Click login helper for hackathon judges to immediately evaluate any of the 3 roles.
   */
  const handleQuickLogin = async (role: 'admin' | 'hr' | 'employee') => {
    await switchMockRole(role);
    navigate(`/${role}/dashboard`);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-accent-foreground font-black text-xl mb-1">
            {companyName.charAt(0).toUpperCase()}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{companyName}</h1>
          <p className="text-xs text-muted-foreground">Minimal, distraction-free Human Capital Management</p>
        </div>

        {/* Credentials Form */}
        <Card className="border border-border">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {errorMsg && (
                <div className="p-3 text-xs bg-rose-500/10 text-rose-600 rounded border border-rose-500/20 font-medium">
                  {errorMsg}
                </div>
              )}

              <Input
                label="Email Address"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
              />

              <Input
                label="Password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />

              <Button type="submit" loading={loading} className="w-full gap-2 mt-2">
                <LogIn className="h-4 w-4" />
                Sign In
              </Button>
            </form>

            {/* Quick 1-Click Role Login Presets for Hackathon Judges */}
            {isMock && (
              <div className="mt-6 pt-6 border-t border-border space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground text-center">
                  Demo 1-Click Role Login
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickLogin('admin')}
                    className="text-xs"
                  >
                    Admin
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickLogin('hr')}
                    className="text-xs"
                  >
                    HR
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickLogin('employee')}
                    className="text-xs"
                  >
                    Employee
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="text-center">
          <p className="text-[11px] text-muted-foreground inline-flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-emerald-500" />
            Protected by Supabase Auth & Scoped Role Access
          </p>
        </div>
      </div>
    </div>
  );
}
