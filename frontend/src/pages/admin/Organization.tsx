/**
 * @file Organization.tsx
 * @description Organization hierarchy & master data configuration (Departments, Designations, Leave Types, Holidays).
 *
 * SPECIFICATION (PROJECT.md section 6 & FARHAN.md):
 * - Departments and Designations CRUD.
 * - Gazetted public holidays management.
 * - Leave Types: features the mandatory "Add default leave types" button to initialize
 *   Annual (14), Sick (8), Casual (10), and Unpaid (unlimited) without automatic seeding.
 */

import React, { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { useToast } from '@/components/ui/Toast';
import { Plus, Trash2, Sparkles, Building2, Briefcase, Calendar, Sun } from 'lucide-react';

export function Organization() {
  const { success, error } = useToast();
  const [activeTab, setActiveTab] = useState<'depts' | 'desigs' | 'leaves' | 'holidays'>('depts');

  const [depts, setDepts] = useState<any[]>([]);
  const [desigs, setDesigs] = useState<any[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<any[]>([]);
  const [holidays, setHolidays] = useState<any[]>([]);

  const [modalOpen, setModalOpen] = useState(false);
  const [itemName, setItemName] = useState('');
  const [extraVal, setExtraVal] = useState<string | number>('');

  /**
   * Loads all organization master data tables in parallel.
   */
  const loadAll = async () => {
    try {
      const [d, ds, lt, h] = await Promise.all([
        api.get<any[]>('/departments'),
        api.get<any[]>('/designations'),
        api.get<any[]>('/leave-types'),
        api.get<any[]>('/holidays'),
      ]);
      if (Array.isArray(d)) setDepts(d);
      if (Array.isArray(ds)) setDesigs(ds);
      if (Array.isArray(lt)) setLeaveTypes(lt);
      if (Array.isArray(h)) setHolidays(h);
    } catch (e) {}
  };

  useEffect(() => {
    loadAll();
  }, []);

  /**
   * Handles creation for the currently active tab category.
   */
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (activeTab === 'depts') {
        await api.post('/departments', { name: itemName });
        success('Department added');
      } else if (activeTab === 'desigs') {
        await api.post('/designations', { name: itemName });
        success('Designation added');
      } else if (activeTab === 'leaves') {
        await api.post('/leave-types', {
          name: itemName,
          yearly_quota: extraVal ? Number(extraVal) : null,
          is_paid: true,
        });
        success('Leave type added');
      } else if (activeTab === 'holidays') {
        await api.post('/holidays', { name: itemName, date: extraVal });
        success('Holiday added');
      }
      setModalOpen(false);
      setItemName('');
      setExtraVal('');
      loadAll();
    } catch (err: any) {
      error(err.message || 'Creation failed');
    }
  };

  /**
   * Installs standard corporate leave types with one click (Annual 14, Sick 8, Casual 10, Unpaid).
   */
  const handleAddDefaultLeaves = async () => {
    try {
      await api.post('/leave-types/defaults');
      success('Default leave quotas (Annual 14, Sick 8, Casual 10, Unpaid) installed.');
      loadAll();
    } catch (err: any) {
      error(err.message || 'Failed to install defaults');
    }
  };

  const handleDeleteDept = async (id: string) => {
    try {
      await api.delete(`/departments/${id}`);
      success('Department deleted');
      loadAll();
    } catch (err: any) {
      error(err.message || 'Delete failed');
    }
  };

  const handleDeleteDesig = async (id: string) => {
    try {
      await api.delete(`/designations/${id}`);
      success('Designation deleted');
      loadAll();
    } catch (err: any) {
      error(err.message || 'Delete failed');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Organization Hierarchy & Master Data"
        description="Manage company departments, job designations, leave types, and gazetted holidays."
        action={
          <div className="flex gap-2">
            {activeTab === 'leaves' && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddDefaultLeaves}
                className="gap-1.5 border-dashed"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Add Default Leave Types
              </Button>
            )}
            <Button size="sm" onClick={() => setModalOpen(true)} className="gap-1.5">
              <Plus className="h-3.5 w-3.5" />
              Add New
            </Button>
          </div>
        }
      />

      {/* Tabs */}
      <div className="flex border-b border-border gap-4 text-xs font-semibold uppercase tracking-wider">
        <button
          onClick={() => setActiveTab('depts')}
          className={`pb-2.5 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'depts'
              ? 'border-accent text-accent'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Building2 className="h-4 w-4" />
          Departments ({depts.length})
        </button>
        <button
          onClick={() => setActiveTab('desigs')}
          className={`pb-2.5 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'desigs'
              ? 'border-accent text-accent'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Briefcase className="h-4 w-4" />
          Designations ({desigs.length})
        </button>
        <button
          onClick={() => setActiveTab('leaves')}
          className={`pb-2.5 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'leaves'
              ? 'border-accent text-accent'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Calendar className="h-4 w-4" />
          Leave Types ({leaveTypes.length})
        </button>
        <button
          onClick={() => setActiveTab('holidays')}
          className={`pb-2.5 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'holidays'
              ? 'border-accent text-accent'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Sun className="h-4 w-4" />
          Holidays ({holidays.length})
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'depts' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Department Directory</CardTitle>
            <CardDescription>Organizational units used for payroll reporting and approvals</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Department Name</TableHead>
                  <TableHead className="w-24 text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {depts.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.name}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteDept(d.id)}
                        className="text-danger hover:bg-danger/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {activeTab === 'desigs' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Designations</CardTitle>
            <CardDescription>Job roles and official employee titles</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Designation Title</TableHead>
                  <TableHead className="w-24 text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {desigs.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.name}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteDesig(d.id)}
                        className="text-danger hover:bg-danger/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {activeTab === 'leaves' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Leave Policy & Quotas</CardTitle>
            <CardDescription>
              Annual balances allowed per calendar year. Leave calculations skip weekends and gazetted holidays.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Leave Type</TableHead>
                  <TableHead>Yearly Quota</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaveTypes.map((lt) => (
                  <TableRow key={lt.id}>
                    <TableCell className="font-medium">{lt.name}</TableCell>
                    <TableCell>
                      {lt.yearly_quota === null ? (
                        <span className="text-muted-foreground italic">Unlimited</span>
                      ) : (
                        `${lt.yearly_quota} days / year`
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="px-2 py-0.5 rounded text-xs bg-surface border border-border">
                        {lt.is_paid ? 'Paid' : 'Unpaid'}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {activeTab === 'holidays' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Gazetted Public Holidays</CardTitle>
            <CardDescription>
              Dates marked here are automatically excluded from working days and leave deductions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Occasion / Holiday Name</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {holidays.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell className="font-medium font-mono text-xs">{h.date}</TableCell>
                    <TableCell>{h.name}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Creation Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={
          activeTab === 'depts'
            ? 'Add Department'
            : activeTab === 'desigs'
            ? 'Add Designation'
            : activeTab === 'leaves'
            ? 'Add Leave Type'
            : 'Add Public Holiday'
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Name / Title"
            required
            value={itemName}
            onChange={(e) => setItemName(e.target.value)}
            placeholder="e.g. Finance, Product Designer, Eid-ul-Fitr"
          />

          {activeTab === 'leaves' && (
            <Input
              label="Yearly Quota (Days)"
              type="number"
              value={extraVal}
              onChange={(e) => setExtraVal(e.target.value)}
              placeholder="Leave empty for unlimited unpaid"
              helperText="Days quota renewed every calendar year"
            />
          )}

          {activeTab === 'holidays' && (
            <Input
              label="Holiday Date"
              type="date"
              required
              value={extraVal as string}
              onChange={(e) => setExtraVal(e.target.value)}
            />
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
