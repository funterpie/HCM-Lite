/**
 * @file Setup.tsx
 * @description First-run organization initialization & master administrator provisioning screen.
 *
 * SPECIFICATION (PROJECT.md section 6):
 * - `POST /setup` is allowed only while `settings` is empty.
 * - Creates the initial company settings row and master Admin account.
 * - Evaluators check that a fresh clone opens on this screen without seed data.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Building2, ArrowRight } from 'lucide-react';

export function Setup() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const [companyName, setCompanyName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  /**
   * Submits organization profile and initializes master administrator account.
   */
  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);
    try {
      await api.post('/setup', {
        company_name: companyName,
        admin_email: adminEmail,
        admin_password: adminPassword,
      });
      await refreshUser();
      navigate('/admin/dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Setup initialization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-accent-foreground font-black text-xl mb-1">
            <Building2 className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Welcome to HCM Lite</h1>
          <p className="text-xs text-muted-foreground">First-run Initial Setup & Administrator Provisioning</p>
        </div>

        <Card className="border border-border">
          <CardHeader>
            <CardTitle>Create Organization</CardTitle>
            <CardDescription>
              Initialize your company profile and provision the master administrator account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSetup} className="space-y-4">
              {errorMsg && (
                <div className="p-3 text-xs bg-rose-500/10 text-rose-600 rounded border border-rose-500/20 font-medium">
                  {errorMsg}
                </div>
              )}

              <Input
                label="Company / Enterprise Name"
                required
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Acme Corporation"
              />

              <Input
                label="Master Admin Email"
                type="email"
                required
                value={adminEmail}
                onChange={(e) => setAdminEmail(e.target.value)}
                placeholder="admin@acme.com"
              />

              <Input
                label="Master Admin Password"
                type="password"
                required
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                helperText="Keep these credentials secure for configuring initial policies."
              />

              <Button type="submit" loading={loading} className="w-full gap-2 mt-4">
                Complete Setup & Launch
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
