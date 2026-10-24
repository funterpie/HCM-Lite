import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { Plus, UserPlus, KeyRound, Shield } from 'lucide-react';

export function Logins() {
  const { success, error } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [tempPassword, setTempPassword] = useState('');

  const [users, setUsers] = useState([
    { id: 'usr-admin-1', email: 'admin@nexustech.com', role: 'admin', is_active: true },
    { id: 'usr-hr-1', email: 'hr@nexustech.com', role: 'hr', is_active: true },
    { id: 'usr-dev-1', email: 'dev@nexustech.com', role: 'employee', is_active: true },
  ]);

  const handleCreateHR = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !tempPassword) {
      error('Please provide email and temporary password');
      return;
    }
    const newUser = {
      id: `usr-hr-${Date.now()}`,
      email,
      role: 'hr',
      is_active: true,
    };
    setUsers([...users, newUser]);
    success(`HR login provisioned for ${email}. Temporary password set.`);
    setModalOpen(false);
    setEmail('');
    setTempPassword('');
  };

  const toggleActive = (id: string) => {
    setUsers(users.map((u) => (u.id === id ? { ...u, is_active: !u.is_active } : u)));
    success('User access status updated.');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Access Control & Login Provisioning"
        description="Manage administrator and HR staff credentials, status, and security keys."
        action={
          <Button onClick={() => setModalOpen(true)} className="gap-2">
            <UserPlus className="h-4 w-4" />
            Provision HR Account
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>System Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-semibold text-xs text-foreground">{u.email}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center gap-1 font-semibold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-muted text-foreground border border-border">
                      <Shield className="h-3 w-3" />
                      {u.role}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-medium border ${
                        u.is_active
                          ? 'bg-emerald-500/10 text-emerald-700 border-emerald-500/30'
                          : 'bg-rose-500/10 text-rose-700 border-rose-500/30'
                      }`}
                    >
                      {u.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleActive(u.id)}
                      className="text-xs"
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Create HR Account">
        <form onSubmit={handleCreateHR} className="space-y-4">
          <Input
            label="Staff Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="hr.officer@company.com"
          />
          <Input
            label="Temporary Password"
            type="password"
            required
            value={tempPassword}
            onChange={(e) => setTempPassword(e.target.value)}
            placeholder="••••••••"
            helperText="The user will be prompted to change their password on first sign in."
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Account</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
