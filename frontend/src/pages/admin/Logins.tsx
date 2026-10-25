import React, { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/auth/AuthProvider';
import { UserPlus, Shield, KeyRound } from 'lucide-react';

interface ManagedUser {
  id: string;
  email: string;
  role: 'admin' | 'hr' | 'employee';
  is_active: boolean;
  must_change_password: boolean;
}

export function Logins() {
  const { success, error } = useToast();
  const { user } = useAuth();
  const [modalOpen, setModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [tempPassword, setTempPassword] = useState('');
  const [resetTarget, setResetTarget] = useState<ManagedUser | null>(null);
  const [resetPassword, setResetPassword] = useState('');
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadUsers = useCallback(async () => {
    try {
      setUsers(await api.get<ManagedUser[]>('/users'));
    } catch (err) {
      error(err instanceof Error ? err.message : 'Could not load user accounts.');
    } finally {
      setLoading(false);
    }
  }, [error]);

  useEffect(() => { void loadUsers(); }, [loadUsers]);

  const handleCreateHR = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await api.post('/users/hr', { email, temp_password: tempPassword });
      success(`HR account created for ${email}. They must change the password after signing in.`);
      setModalOpen(false);
      setEmail('');
      setTempPassword('');
      await loadUsers();
    } catch (err) {
      error(err instanceof ApiError ? err.message : 'Could not create the HR account.');
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (managedUser: ManagedUser) => {
    try {
      await api.patch(`/users/${managedUser.id}/active`, { is_active: !managedUser.is_active });
      success(`Account ${managedUser.is_active ? 'deactivated' : 'activated'}.`);
      await loadUsers();
    } catch (err) {
      error(err instanceof ApiError ? err.message : 'Could not update account access.');
    }
  };

  const handlePasswordReset = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!resetTarget) return;
    setSaving(true);
    try {
      await api.post(`/users/${resetTarget.id}/reset-password`, { temp_password: resetPassword });
      success(`Password reset for ${resetTarget.email}. They must change it after signing in.`);
      setResetTarget(null);
      setResetPassword('');
      await loadUsers();
    } catch (err) {
      error(err instanceof ApiError ? err.message : 'Could not reset this password.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Access Control & Login Provisioning"
        description="Manage administrator, HR, and employee account access."
        action={<Button onClick={() => setModalOpen(true)} className="gap-2"><UserPlus className="h-4 w-4" />Provision HR Account</Button>}
      />
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader><TableRow><TableHead>Email</TableHead><TableHead>System Role</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {loading ? <TableRow><TableCell colSpan={4}>Loading accounts…</TableCell></TableRow> : users.map((managedUser) => (
                <TableRow key={managedUser.id}>
                  <TableCell className="font-semibold text-xs text-foreground">{managedUser.email}</TableCell>
                  <TableCell><span className="inline-flex items-center gap-1 font-semibold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-muted text-foreground border border-border"><Shield className="h-3 w-3" />{managedUser.role}</span></TableCell>
                  <TableCell><span className={`px-2 py-0.5 rounded-full text-[11px] font-medium border ${managedUser.is_active ? 'bg-emerald-500/10 text-emerald-700 border-emerald-500/30' : 'bg-rose-500/10 text-rose-700 border-rose-500/30'}`}>{managedUser.is_active ? 'Active' : 'Disabled'}{managedUser.must_change_password ? ' · Password change required' : ''}</span></TableCell>
                  <TableCell className="text-right space-x-2"><Button variant="outline" size="sm" onClick={() => { setResetTarget(managedUser); setResetPassword(''); }} className="text-xs gap-1"><KeyRound className="h-3 w-3" />Reset password</Button><Button variant="outline" size="sm" onClick={() => void toggleActive(managedUser)} className="text-xs" disabled={managedUser.id === user?.id}>{managedUser.is_active ? 'Deactivate' : 'Activate'}</Button></TableCell>
                </TableRow>
              ))}
              {!loading && users.length === 0 && <TableRow><TableCell colSpan={4}>No accounts found.</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Create HR Account">
        <form onSubmit={handleCreateHR} className="space-y-4">
          <Input label="Staff Email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="hr.officer@company.com" />
          <Input label="Temporary Password" type="password" required minLength={8} value={tempPassword} onChange={(event) => setTempPassword(event.target.value)} placeholder="At least 8 characters" helperText="The user will be required to change this password after signing in." />
          <div className="flex justify-end gap-2 pt-2"><Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button><Button type="submit" loading={saving}>Create Account</Button></div>
        </form>
      </Modal>
      <Modal isOpen={resetTarget !== null} onClose={() => setResetTarget(null)} title="Reset Account Password">
        <form onSubmit={handlePasswordReset} className="space-y-4">
          <p className="text-sm text-muted-foreground">Set a temporary password for {resetTarget?.email}. They will be asked to change it at next sign-in.</p>
          <Input label="Temporary Password" type="password" required minLength={8} value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} placeholder="At least 8 characters" />
          <div className="flex justify-end gap-2 pt-2"><Button type="button" variant="outline" onClick={() => setResetTarget(null)}>Cancel</Button><Button type="submit" loading={saving}>Reset Password</Button></div>
        </form>
      </Modal>
    </div>
  );
}
