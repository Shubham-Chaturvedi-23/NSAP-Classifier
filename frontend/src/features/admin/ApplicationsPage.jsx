import React, { useState, useEffect } from "react";
import { adminApi } from '../../api/admin.api';
import { fmtDate, getStatusLabel } from '../../utils/formatters';
import { STATUS_BADGE_MAP, SCHEME_LABELS, APPLICATION_STATUS } from '../../utils/constants';

export default function AdminApplicationsPage() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [schemeFilter, setSchemeFilter] = useState('');
  const [offset, setOffset] = useState(0);

  const LIMIT = 20;

  useEffect(() => {
    setLoading(true);

    const params = { limit: LIMIT, offset };
    if (statusFilter) params.status_filter = statusFilter;
    if (schemeFilter) params.scheme_filter = schemeFilter;

    adminApi.getApplications(params)
      .then((r) => {

        const data = r?.data;

        let list = [];

        if (Array.isArray(data)) list = data;
        else if (Array.isArray(data?.applications)) list = data.applications;
        else if (Array.isArray(data?.items)) list = data.items;
        else if (Array.isArray(data?.data)) list = data.data;

        setApps(list);
      })
      .catch(() => setApps([]))
      .finally(() => setLoading(false));

  }, [statusFilter, schemeFilter, offset]);

  const safeApps = Array.isArray(apps) ? apps : [];

  return (
    <div>
      <div className="page-header">
        <h1>Applications Explorer</h1>
        <p>All applications across the system</p>
      </div>

      <div className="card" style={{ padding: '14px 18px', marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setOffset(0); }}
          style={{ width: 180 }}
        >
          <option value="">All Statuses</option>
          {Object.values(APPLICATION_STATUS).map((s) =>
            <option key={s} value={s}>{getStatusLabel(s)}</option>
          )}
        </select>

        <select
          value={schemeFilter}
          onChange={(e) => { setSchemeFilter(e.target.value); setOffset(0); }}
          style={{ width: 180 }}
        >
          <option value="">All Schemes</option>
          {Object.entries(SCHEME_LABELS).map(([k, v]) =>
            <option key={k} value={k}>{v}</option>
          )}
        </select>

        <button
          className="btn btn-secondary"
          onClick={() => { setStatusFilter(''); setSchemeFilter(''); setOffset(0); }}
          style={{ marginLeft: 'auto' }}
        >
          Clear
        </button>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="loading"><div className="spinner" /></div>
        ) : safeApps.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📂</div>
            <h3>No applications found</h3>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Submitted</th>
                  <th>Citizen</th>
                  <th>Predicted Scheme</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Decision</th>
                </tr>
              </thead>

              <tbody>
                {safeApps.map((a) => (
                  <tr key={a.id}>
                    <td>#{a.id}</td>
                    <td>{fmtDate(a.submitted_at || a.created_at)}</td>
                    <td>{a.citizen_name || a.citizen_email || '—'}</td>

                    <td>
                      {SCHEME_LABELS[a?.prediction?.predicted_scheme] ||
                        a?.prediction?.predicted_scheme ||
                        SCHEME_LABELS[a?.predicted_scheme] ||
                        a?.predicted_scheme ||
                        '—'}
                    </td>

                    <td>
                      {(a?.prediction?.confidence_score ?? a?.confidence_score) != null
                        ? `${Math.round((a?.prediction?.confidence_score ?? a?.confidence_score) * 100)}%`
                        : '—'}
                    </td>

                    <td>
                      <span className={`badge ${STATUS_BADGE_MAP[a.status] || 'badge-pending'}`}>
                        {getStatusLabel(a.status)}
                      </span>
                    </td>

                    <td>
                      {a?.has_decision
                        ? <span className="badge badge-review">Recorded</span>
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {safeApps.length > 0 && (
          <div className="pagination">
            <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>
              ← Prev
            </button>

            <span className="page-info">
              {offset + 1}–{offset + safeApps.length}
            </span>

            <button disabled={safeApps.length < LIMIT} onClick={() => setOffset(offset + LIMIT)}>
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}