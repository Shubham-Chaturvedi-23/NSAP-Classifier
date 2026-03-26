import React, { useState, useEffect } from "react";
import { adminApi } from '../../api/admin.api';
import { useTranslation } from 'react-i18next';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#f0883e', '#388bfd', '#3fb950', '#f85149', '#d29922'];

export default function AdminDashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([adminApi.getStats(), adminApi.getOfficerActivity()])
      .then(([s, a]) => {
        setStats(s.data);
        setActivity(a.data?.officers || a.data || []);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  const schemeData = stats?.applications?.by_scheme
    ? Object.entries(stats.applications.by_scheme).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const statusData = stats?.applications?.by_status
    ? Object.entries(stats.applications.by_status).map(([k, v]) => ({ name: k, value: v }))
    : [];

  return (
    <div>
      <div className="page-header">
        <h1>{t('admin.dashboard')}</h1>
        <p>{t('admin.dashboard_sub')}</p>
      </div>

      {/* Summary stats */}
      {stats && (
        <div className="grid-4" style={{ marginBottom: 24 }}>
          {[
            { label: t('admin.total_apps'), value: stats.applications?.total ?? '—', icon: '📋', color: 'var(--accent2)' },
            { label: t('admin.pending_review'), value: stats.applications?.by_status?.needs_review ?? stats.applications?.by_status?.pending ?? '—', icon: '⏳', color: 'var(--warning)' },
            { label: t('admin.approved'), value: stats.applications?.by_status?.approved ?? '—', icon: '✅', color: 'var(--success)' },
            { label: 'Avg Confidence', value: stats.model?.avg_confidence != null ? `${(stats.model.avg_confidence * 100).toFixed(1)}%` : '—', icon: '🤖', color: 'var(--accent)' },
          ].map((s) => (
            <div key={s.label} className="card stat-card">
              <div className="label" style={{ color: s.color }}>{s.icon} {s.label}</div>
              <div className="value">{s.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Scheme distribution */}
        {schemeData.length > 0 && (
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>
              Scheme Distribution
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={schemeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                  {schemeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Status distribution */}
        {statusData.length > 0 && (
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>
              Status Distribution
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={statusData} barSize={28}>
                <XAxis dataKey="name" tick={{ fill: 'var(--text2)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--text2)', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)' }} />
                <Bar dataKey="value" fill="var(--accent2)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Officer activity leaderboard */}
      {activity.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>
            🏆 Officer Activity Leaderboard
          </h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Officer</th>
                  <th>Total Reviewed</th>
                  <th>Approved</th>
                  <th>Rejected</th>
                  <th>Avg Decision Time</th>
                </tr>
              </thead>
              <tbody>
                {activity.map((o, i) => (
                  <tr key={o.officer_id || o.id}>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 12, color: i < 3 ? 'var(--warning)' : 'var(--text2)' }}>
                      {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                    </td>
                    <td style={{ fontWeight: 600 }}>{o.name || o.officer_name || `Officer #${o.officer_id}`}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{o.total_reviewed ?? o.total_decisions ?? o.total ?? '—'}</td>
                    <td style={{ color: 'var(--success)', fontFamily: 'var(--mono)' }}>{o.approved ?? '—'}</td>
                    <td style={{ color: 'var(--danger)', fontFamily: 'var(--mono)' }}>{o.rejected ?? '—'}</td>
                    <td style={{ color: 'var(--text2)', fontSize: 13 }}>{o.avg_decision_time ?? o.decisions_today ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}