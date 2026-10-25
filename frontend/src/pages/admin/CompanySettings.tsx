/**
 * @file CompanySettings.tsx
 * @description Company configuration and business rules management screen.
 *
 * SPECIFICATION (PROJECT.md section 7):
 * - Company name & timezone (default 'Asia/Karachi').
 * - Office start (09:00), grace period (15 min), half day threshold (under 5h).
 * - Office latitude, longitude, and geofencing radius (150m).
 * - Late arrival penalty toggle (3 lates = 0.5 day deduction).
 * - Admin has PUT access; settings apply strictly to new records.
 */

import React, { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { useToast } from '@/components/ui/Toast';
import { Skeleton } from '@/components/ui/Skeleton';
import { Save, MapPin, Clock } from 'lucide-react';

export function CompanySettings() {
  const { success, error } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<any>({
    company_name: '',
    timezone: 'Asia/Karachi',
    office_start: '09:00',
    grace_minutes: 15,
    half_day_hours: 5,
    office_lat: 24.8607,
    office_lng: 67.0011,
    office_radius_m: 150,
    late_penalty_enabled: false,
  });

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get('/settings');
        if (res) setSettings(res);
      } catch (e) {
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  /**
   * Persists company policy updates to `PUT /settings`.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put('/settings', settings);
      success('Company policies and settings saved successfully.');
    } catch (err: any) {
      error(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Company Settings & Policies"
        description="Configure work hours, grace periods, geofencing parameters, and payroll penalties."
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* General Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">General Profile</CardTitle>
            <CardDescription>Enterprise identity and default regional timezone</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Company Name"
                required
                value={settings.company_name}
                onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
              />
              <Input
                label="System Timezone"
                required
                value={settings.timezone}
                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                helperText="All server attendance stamps use this timezone."
              />
            </div>
          </CardContent>
        </Card>

        {/* Attendance Timing Rules */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              <CardTitle className="text-sm">Attendance & Grace Rules</CardTitle>
            </div>
            <CardDescription>Rules applied strictly to check-in stamps on the server</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Office Start Time"
                type="time"
                required
                value={settings.office_start}
                onChange={(e) => setSettings({ ...settings, office_start: e.target.value })}
              />
              <Input
                label="Grace Period (Minutes)"
                type="number"
                min={0}
                required
                value={settings.grace_minutes}
                onChange={(e) => setSettings({ ...settings, grace_minutes: Number(e.target.value) })}
                helperText="Late mark starts strictly at start + grace (09:16)."
              />
              <Input
                label="Half-Day Threshold (Hours)"
                type="number"
                step="0.5"
                min={1}
                required
                value={settings.half_day_hours}
                onChange={(e) => setSettings({ ...settings, half_day_hours: Number(e.target.value) })}
                helperText="Worked hours under this trigger half-day."
              />
            </div>

            <div className="pt-2 border-t border-border flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-foreground">Enable Late Arrival Penalty</p>
                <p className="text-[11px] text-muted-foreground">3 late check-ins deduct 0.5 day during monthly payroll.</p>
              </div>
              <input
                type="checkbox"
                checked={settings.late_penalty_enabled}
                onChange={(e) => setSettings({ ...settings, late_penalty_enabled: e.target.checked })}
                className="h-4 w-4 rounded border-border accent-accent cursor-pointer"
              />
            </div>
          </CardContent>
        </Card>

        {/* Geofence Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              <CardTitle className="text-sm">Office Location & Geofencing</CardTitle>
            </div>
            <CardDescription>Used to validate camera & mobile GPS attendance check-ins</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Latitude"
                type="number"
                step="any"
                value={settings.office_lat || ''}
                onChange={(e) => setSettings({ ...settings, office_lat: parseFloat(e.target.value) })}
              />
              <Input
                label="Longitude"
                type="number"
                step="any"
                value={settings.office_lng || ''}
                onChange={(e) => setSettings({ ...settings, office_lng: parseFloat(e.target.value) })}
              />
              <Input
                label="Allowed Radius (Meters)"
                type="number"
                value={settings.office_radius_m || 150}
                onChange={(e) => setSettings({ ...settings, office_radius_m: parseInt(e.target.value) })}
                helperText="Default: 150 meters from center"
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" loading={saving} className="gap-2">
            <Save className="h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
}
