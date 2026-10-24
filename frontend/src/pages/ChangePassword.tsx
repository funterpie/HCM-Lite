import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { KeyRound, ShieldAlert } from 'lucide-react';

export function ChangePassword() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (newPassword.length < 8) {
      setErrorMsg('Password must be at least 8 characters long');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/change-password', { new_password: newPassword });
      await refreshUser();
      navigate(user ? `/${user.role}/dashboard` : '/login');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600 font-black text-xl mb-1">
            <KeyRound className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">Password Update Required</h1>
          <p className="text-xs text-muted-foreground">
            You are logged in with a temporary credentials. Please set a new permanent password.
          </p>
        </div>

        <Card className="border border-border">
          <CardHeader>
            <div className="flex items-center gap-2 text-xs text-amber-600 font-medium bg-amber-500/10 p-2.5 rounded">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              <span>For your account security, you must update your password before proceeding.</span>
            </div>
            <CardTitle className="mt-2">Set New Password</CardTitle>
            <CardDescription>Choose a strong password with at least 8 characters.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {errorMsg && (
                <div className="p-3 text-xs bg-rose-500/10 text-rose-600 rounded border border-rose-500/20 font-medium">
                  {errorMsg}
                </div>
              )}

              <Input
                label="New Password"
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
              />

              <Input
                label="Confirm Password"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
              />

              <Button type="submit" loading={loading} className="w-full mt-2">
                Update Password & Continue
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
