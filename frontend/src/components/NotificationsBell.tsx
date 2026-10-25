/**
 * @file NotificationsBell.tsx
 * @description Header bell icon displaying live unread notifications count, dropdown list,
 * and mark-as-read interaction via `PATCH /notifications/{id}/read`.
 */

import { useState, useEffect } from 'react';
import { Bell, Check } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from './ui/Button';

export interface NotificationItem {
  id: string;
  title: string;
  body?: string;
  read: boolean;
  created_at: string;
}

export function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  /**
   * Fetches the user's personal notifications list.
   */
  const fetchNotifs = async () => {
    try {
      const res = await api.get<NotificationItem[]>('/notifications');
      if (Array.isArray(res)) setNotifications(res);
    } catch (e) {}
  };

  useEffect(() => {
    fetchNotifs();
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  /**
   * Marks a notification as read and updates local state.
   */
  const markAsRead = async (id: string) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    } catch (e) {}
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen(!open)}
        className="relative text-foreground hover:bg-surface"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg border border-border bg-surface-elevated shadow-xl z-50 p-2 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between p-2 border-b border-border/50">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Notifications</span>
            {unreadCount > 0 && (
              <span className="text-[10px] bg-rose-500/10 text-rose-600 px-1.5 py-0.5 rounded font-medium">
                {unreadCount} new
              </span>
            )}
          </div>
          <div className="max-h-72 overflow-y-auto divide-y divide-border/40 py-1">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-xs text-muted-foreground">No notifications</div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3 text-xs transition-colors rounded ${
                    n.read ? 'opacity-70 hover:opacity-100' : 'bg-surface font-medium'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-foreground font-semibold">{n.title}</p>
                    {!n.read && (
                      <button
                        onClick={() => markAsRead(n.id)}
                        className="text-muted-foreground hover:text-foreground shrink-0"
                        title="Mark as read"
                      >
                        <Check className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                  {n.body && <p className="text-muted-foreground mt-1 text-[11px] leading-relaxed">{n.body}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
