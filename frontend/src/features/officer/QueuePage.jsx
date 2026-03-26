import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { officerApi } from "../../api/officer.api";
import { useToast } from "../../app/providers";
import { fmtDate, getStatusLabel } from "../../utils/formatters";
import { STATUS_BADGE_MAP, SCHEME_LABELS } from "../../utils/constants";

export default function OfficerQueuePage() {
  const { addToast } = useToast();
  const [queue, setQueue] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOtherIds, setSelectedOtherIds] = useState([]);
  const [bulkApproving, setBulkApproving] = useState(false);

  const loadQueue = () => {
    setLoading(true);
    Promise.all([
      officerApi.getQueue({ limit: 20, offset: 0 }),
      officerApi.getStats(),
    ])
      .then(([q, s]) => {
        const data = q?.data;

        let list = [];

        if (Array.isArray(data)) list = data;
        else if (Array.isArray(data?.queue)) list = data.queue;
        else if (Array.isArray(data?.applications)) list = data.applications;
        else if (Array.isArray(data?.items)) list = data.items;
        else if (Array.isArray(data?.data)) list = data.data;

        setQueue(list);
        setStats(s?.data || null);
        setSelectedOtherIds([]);
      })
      .catch(() => {
        setQueue([]);
        setStats(null);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const safeQueue = Array.isArray(queue) ? queue : [];

  const needsReview = safeQueue.filter(
    (a) => a?.prediction?.needs_review || a?.status === "needs_review"
  );

  const autoApproved = safeQueue.filter((a) => a?.status === "auto_approved");

  const toggleOtherSelection = (id) => {
    setSelectedOtherIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAllOthers = () => {
    setSelectedOtherIds(autoApproved.map((a) => a.id));
  };

  const clearOtherSelection = () => {
    setSelectedOtherIds([]);
  };

  const approveSelectedOthers = async () => {
    if (!selectedOtherIds.length) {
      addToast("Select at least one application first.", "info");
      return;
    }

    setBulkApproving(true);
    try {
      const results = await Promise.allSettled(
        selectedOtherIds.map((id) =>
          officerApi.decide(id, {
            application_id: id,
            decision: "approved",
            remarks: "Bulk approved from officer review queue.",
          })
        )
      );

      const successCount = results.filter((r) => r.status === "fulfilled").length;
      const failCount = results.length - successCount;

      if (successCount > 0) {
        addToast(`${successCount} application(s) approved.`, "success");
      }
      if (failCount > 0) {
        addToast(`${failCount} application(s) could not be approved.`, "error");
      }

      loadQueue();
    } finally {
      setBulkApproving(false);
    }
  };

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
              value: stats.queue?.total_pending ?? stats.total ?? "—",
              icon: "📋",
            },
            {
              label: "Pending Review",
              value: stats.queue?.needs_review ?? stats.pending ?? "—",
              icon: "⏳",
            },
            { label: "Approved", value: stats.my_decisions?.approved ?? "—", icon: "✅" },
            { label: "Rejected", value: stats.my_decisions?.rejected ?? "—", icon: "❌" },
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
          Auto Approved Applications{" "}
          {autoApproved.length > 0 && `(${autoApproved.length})`}
        </div>

        {autoApproved.length === 0 && needsReview.length === 0 ? (
          <div className="empty-state card">
            <div className="icon">🎉</div>
            <h3>Queue is empty</h3>
            <p>All applications have been processed</p>
          </div>
        ) : autoApproved.length > 0 ? (
          <>
            <div className="card" style={{ marginBottom: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <button className="btn btn-secondary" onClick={selectAllOthers} disabled={bulkApproving}>
                Select All
              </button>
              <button className="btn btn-secondary" onClick={clearOtherSelection} disabled={bulkApproving || !selectedOtherIds.length}>
                Clear Selection
              </button>
              <button className="btn btn-success" onClick={approveSelectedOthers} disabled={bulkApproving || !selectedOtherIds.length}>
                {bulkApproving ? "Approving..." : `Approve Selected (${selectedOtherIds.length})`}
              </button>
            </div>
            <div className="card" style={{ padding: 0 }}>
              <AppTable
                rows={autoApproved}
                selectable
                selectedIds={selectedOtherIds}
                onToggleSelect={toggleOtherSelection}
              />
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function AppTable({ rows, highlight, selectable = false, selectedIds = [], onToggleSelect }) {
  const safeRows = Array.isArray(rows) ? rows : [];

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {selectable && <th>Select</th>}
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
              {selectable && (
                <td>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(a.id)}
                    onChange={() => onToggleSelect?.(a.id)}
                  />
                </td>
              )}
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

              <td>{fmtDate(a.submitted_at || a.created_at)}</td>

              <td>
                <span style={{ fontWeight: 600 }}>
                  {SCHEME_LABELS[a?.prediction?.predicted_scheme] ||
                    a?.prediction?.predicted_scheme ||
                    SCHEME_LABELS[a?.predicted_scheme] ||
                    a?.predicted_scheme ||
                    "—"}
                </span>
              </td>

              <td>
                {(a?.prediction?.confidence_score ?? a?.confidence_score) != null
                  ? `${Math.round((a?.prediction?.confidence_score ?? a?.confidence_score) * 100)}%`
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