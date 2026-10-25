/**
 * @file MyProfile.tsx
 * @description Personal contact profile editor for employees.
 *
 * SPECIFICATION (PROJECT.md section 8 & FARHAN_GUIDE.txt Task F13):
 * - Staff can self-manage contact details (phone, residential address) via `PATCH /me/profile`.
 * - Department, designation, and compensation are read-only and require HR authorization.
 */

import React, { useState } from 'react';
import { api } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { useToast } from '@/components/ui/Toast';
import { Save, User } from 'lucide-react';

export function MyProfile() {
  const { user } = useAuth();
  const { success, error } = useToast();

  const [phone, setPhone] = useState('+92 333 9988776');
  const [address, setAddress] = useState('Gulshan-e-Iqbal, Block 4, Karachi');
  const [saving, setSaving] = useState(false);

  /**
   * Persists phone and address updates to `PATCH /me/profile`.
   */
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch('/me/profile', { phone, address });
      success('Contact details updated successfully.');
    } catch (err: any) {
      error(err.message || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader
        title="Personal Profile & Contact Information"
        description="Employees may update phone and residential address directly. Official job title and compensation require HR approval."
      />

      <form onSubmit={handleSave} className="space-y-6">
        {/* Account Identifier Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4" />
              <CardTitle className="text-sm">Account Overview</CardTitle>
            </div>
            <CardDescription>System identifiers and verified email</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground block">Email</span>
                <p className="font-semibold text-xs mt-1">{user?.email}</p>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground block">Role</span>
                <span className="inline-block mt-1 font-semibold uppercase text-[10px] px-2 py-0.5 rounded bg-muted text-foreground border border-border">
                  {user?.role}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Editable Contact Fields */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Editable Contact Details</CardTitle>
            <CardDescription>Keep emergency contact details up to date</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Contact Phone Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+92 300 1234567"
            />
            <Input
              label="Current Residential Address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Apartment, Street, City"
            />
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" loading={saving} className="gap-2">
            <Save className="h-4 w-4" />
            Update Profile
          </Button>
        </div>
      </form>
    </div>
  );
}
