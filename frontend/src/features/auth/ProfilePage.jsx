import React, { useState, useEffect } from "react";
import { useAuth, useToast } from '../../app/providers';
import { useTranslation } from 'react-i18next';
import { authApi } from '../../api/auth.api';

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const { addToast } = useToast();
  const [form, setForm] = useState({ name: user?.name || '', phone: user?.phone || '', address: user?.address || '', state: user?.state || '' });
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.updateMe(form);
      await refreshUser();
      addToast(t('auth.profile_updated'), 'success');
    } catch {
      addToast(t('auth.update_failed'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 560 }}>
      <div className="page-header">
        <h1>{t('auth.profile_title')}</h1>
        <p>{t('auth.profile_sub')}</p>
      </div>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28, paddingBottom: 20, borderBottom: '1px solid var(--border)' }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 800, color: '#fff' }}>
            {(user?.name || user?.email || '?')[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>{user?.name || '—'}</div>
            <div style={{ color: 'var(--text2)', fontSize: 13 }}>{user?.email}</div>
            <span className={`role-badge role-${user?.role}`} style={{ marginTop: 6, display: 'inline-block' }}>{user?.role?.toUpperCase()}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label>{t('auth.full_name')}</label>
              <input value={form.name} onChange={set('name')} placeholder={t('auth.your_name')} />
            </div>
            <div className="form-group">
              <label>{t('auth.phone')}</label>
              <input value={form.phone} onChange={set('phone')} placeholder={t('auth.phone_format')} />
            </div>
          </div>
          <div className="form-group">
            <label>{t('auth.state')}</label>
            <input value={form.state} onChange={set('state')} placeholder={t('auth.your_state')} />
          </div>
          <div className="form-group">
            <label>Address</label>
            <textarea rows={3} value={form.address} onChange={set('address')} placeholder="Your address" style={{ resize: 'vertical' }} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving…' : '💾 Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
}