import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { officerApi } from "../../api/officer.api";
import { fmtDate, getStatusLabel } from "../../utils/formatters";
import { STATUS_BADGE_MAP, SCHEME_LABELS } from "../../utils/constants";

export default function OfficerQueuePage() {
  const [queue, setQueue] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      officerApi.getQueue({ limit: 20, offset: 0 }),
      officerApi.getStats(),
    ])
      .then(([q, s]) => {
        const data = q?.data;

        let list = [];

        if (Array.isArray(data)) list = data;
        else if (Array.isArray(data?.applications)) list = data.applications;
        else if (Array.isArray(data?.items)) list = data.items;
        else if (Array.isArray(data?.data)) list = data.data;

        setQueue(list);
        setStats(s?.data || null);
      })
      .catch(() => {
        setQueue([]);
        setStats(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const safeQueue = Array.isArray(queue) ? queue : [];

  const needsReview = safeQueue.filter(
    (a) => a?.prediction?.needs_review || a?.status === "needs_review"
  );

  const others = safeQueue.filter(
    (a) => !(a?.prediction?.needs_review || a?.status === "needs_review")
  );

  if (loading)
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    );

  return (
    <div>
      <div className="page-header">
        <h1>Review Queue</h1>
        <p>Applications requiring officer review</p>
      </div>

      {stats && (
        <div className="grid-4" style={{ marginBottom: 24 }}>
          {[
            {
              label: "Total Assigned",
              value: stats.total_assigned ?? stats.total ?? "—",
              icon: "📋",
            },
            {
              label: "Pending Review",
              value: stats.pending_review ?? stats.pending ?? "—",
              icon: "⏳",
            },
            { label: "Approved", value: stats.approved ?? "—", icon: "✅" },
            { label: "Rejected", value: stats.rejected ?? "—", icon: "❌" },
          ].map((s) => (
            <div key={s.label} className="card stat-card">
              <div className="label">
                {s.icon} {s.label}
              </div>
              <div className="value">{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {needsReview.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 12,
            }}
          >
            <span
              style={{
                fontSize: 14,
                fontWeight: 700,
                color: "var(--warning)",
              }}
            >
              ⚠️ High Priority — Needs Review
            </span>
            <span className="badge badge-review">{needsReview.length}</span>
          </div>
          <div
            className="card"
            style={{ padding: 0, borderColor: "rgba(210,153,34,0.3)" }}
          >
            <AppTable rows={needsReview} highlight />
          </div>
        </div>
      )}

      <div>
        <div
          style={{
            fontSize: 14,
            fontWeight: 700,
            color: "var(--text2)",
            marginBottom: 12,
          }}
        >
          Other Pending Applications{" "}
          {others.length > 0 && `(${others.length})`}
        </div>

        {others.length === 0 && needsReview.length === 0 ? (
          <div className="empty-state card">
            <div className="icon">🎉</div>
            <h3>Queue is empty</h3>
            <p>All applications have been processed</p>
          </div>
        ) : others.length > 0 ? (
          <div className="card" style={{ padding: 0 }}>
            <AppTable rows={others} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function AppTable({ rows, highlight }) {
  const safeRows = Array.isArray(rows) ? rows : [];

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>App ID</th>
            <th>Submitted</th>
            <th>Predicted Scheme</th>
            <th>Confidence</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {safeRows.map((a) => (
            <tr
              key={a.id}
              style={highlight ? { background: "rgba(210,153,34,0.04)" } : {}}
            >
              <td>
                <span
                  style={{
                    fontFamily: "var(--mono)",
                    fontSize: 12,
                    color: "var(--text2)",
                  }}
                >
                  #{a.id}
                </span>
              </td>

              <td>{fmtDate(a.created_at)}</td>

              <td>
                <span style={{ fontWeight: 600 }}>
                  {SCHEME_LABELS[a?.prediction?.predicted_scheme] ||
                    a?.prediction?.predicted_scheme ||
                    "—"}
                </span>
              </td>

              <td>
                {a?.prediction?.confidence_score != null
                  ? `${Math.round(a.prediction.confidence_score * 100)}%`
                  : "—"}
              </td>

              <td>
                <span
                  className={`badge ${
                    STATUS_BADGE_MAP[a.status] || "badge-pending"
                  }`}
                >
                  {getStatusLabel(a.status)}
                </span>
              </td>

              <td>
                <Link
                  to={`/officer/applications/${a.id}`}
                  className="btn btn-primary"
                  style={{ padding: "6px 14px", fontSize: 12 }}
                >
                  Review →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}