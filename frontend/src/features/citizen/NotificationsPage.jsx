import React, { useState, useEffect } from "react";
import { citizenApi } from '../../api/citizen.api';
import { useToast } from '../../app/providers';
import { fmtDateTime } from '../../utils/formatters';

export default function NotificationsPage() {
  const { addToast } = useToast();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    citizenApi.getNotifications({ limit: 50, offset: 0 })
      .then((r) => setNotifications(r.data?.notifications || r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const markAll = async () => {
    try {
      await citizenApi.markAllRead();
      load();
      addToast('All notifications marked as read.', 'success');
    } catch { addToast('Failed.', 'error'); }
  };

  const markOne = async (id) => {
    try {
      await citizenApi.markRead(id);
      setNotifications((n) => n.map((x) => x.id === id ? { ...x, is_read: true } : x));
    } catch {}
  };

  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <div style={{ maxWidth: 680 }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1>Notifications</h1>
          <p>{unread > 0 ? `${unread} unread` : 'All caught up'}</p>
        </div>
        {unread > 0 && (
          <button className="btn btn-secondary" onClick={markAll}>✓ Mark all read</button>
        )}
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : notifications.length === 0 ? (
        <div className="empty-state">
          <div className="icon">🔔</div>
          <h3>No notifications</h3>
          <p>You'll be notified when your application status changes</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {notifications.map((n) => (
            <div
              key={n.id}
              className="card"
              style={{
                padding: '14px 18px',
                display: 'flex', alignItems: 'flex-start', gap: 14,
                borderLeft: n.is_read ? '3px solid var(--border)' : '3px solid var(--accent2)',
                cursor: n.is_read ? 'default' : 'pointer',
                opacity: n.is_read ? 0.7 : 1,
              }}
              onClick={() => !n.is_read && markOne(n.id)}
            >
              <span style={{ fontSize: 20, marginTop: 2 }}>
                {n.type === 'status_update' ? '📋' : n.type === 'decision' ? '⚖️' : '🔔'}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: n.is_read ? 400 : 700, fontSize: 14 }}>{n.message || n.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 4 }}>{fmtDateTime(n.created_at)}</div>
              </div>
              {!n.is_read && (
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent2)', marginTop: 6, flexShrink: 0 }} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}