import React, { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { formatDate } from '@/lib/utils';
import { Megaphone, Plus, Calendar, User } from 'lucide-react';

export function AnnouncementsPage() {
  const { user } = useAuth();
  const { success, error } = useToast();
  const canPost = user?.role === 'admin' || user?.role === 'hr';

  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAnnouncements = async () => {
    try {
      const res = await api.get<any[]>('/announcements');
      if (Array.isArray(res)) setAnnouncements(res);
    } catch (e) {}
  };

  useEffect(() => {
    loadAnnouncements();
  }, []);

  const handlePost = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/announcements', { title, body });
      success('Company announcement broadcasted.');
      setModalOpen(false);
      setTitle('');
      setBody('');
      loadAnnouncements();
    } catch (err: any) {
      error(err.message || 'Posting failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Company Announcements"
        description="Official circulars, organizational updates, and executive notices."
        action={
          canPost && (
            <Button size="sm" onClick={() => setModalOpen(true)} className="gap-1.5">
              <Plus className="h-4 w-4" />
              Broadcast Notice
            </Button>
          )
        }
      />

      <div className="space-y-4">
        {announcements.map((a) => (
          <Card key={a.id} className="border border-border">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-semibold">{a.title}</CardTitle>
                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-mono">
                  <Calendar className="h-3 w-3" />
                  {formatDate(a.created_at)}
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                <User className="h-3 w-3" />
                <span>Posted by {a.posted_by_name || 'HR Management'}</span>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap">{a.body}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Create Company Announcement"
      >
        <form onSubmit={handlePost} className="space-y-4">
          <Input
            label="Notice Title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Annual Sports Gala / Office Closure"
          />
          <Textarea
            label="Message Body"
            required
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Enter announcement details..."
            rows={4}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={submitting}>
              Publish Announcement
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
