import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { citizenApi } from "../../api/citizen.api";
import { fmtDate, getStatusLabel } from "../../utils/formatters";
import { STATUS_BADGE_MAP, SCHEME_LABELS } from "../../utils/constants";

export default function CitizenApplicationsPage() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const LIMIT = 10;

  useEffect(() => {
    setLoading(true);

    citizenApi
      .getApplications({ limit: LIMIT, offset })
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
  }, [offset]);

  return (
    <div>
      <div
        className="page-header"
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
        }}
      >
        <div>
          <h1>My Applications</h1>
          <p>Track your scheme applications and their status</p>
        </div>
        <Link to="/citizen/apply" className="btn btn-primary">
          ✏️ New Application
        </Link>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
        ) : !Array.isArray(apps) || apps.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📋</div>
            <h3>No applications yet</h3>
            <p>Submit your first application to get started</p>
            <Link
              to="/citizen/apply"
              className="btn btn-primary"
              style={{ marginTop: 16 }}
            >
              Apply Now
            </Link>
          </div>
        ) : (
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
                {Array.isArray(apps) &&
                  apps.map((a) => (
                    <tr key={a.id}>
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
                        {a.prediction ? (
                          <span style={{ fontWeight: 600 }}>
                            {SCHEME_LABELS[
                              a.prediction.predicted_scheme
                            ] || a.prediction.predicted_scheme}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>

                      <td>
                        {a.prediction?.confidence_score != null ? (
                          <ConfidenceBar
                            value={a.prediction.confidence_score}
                          />
                        ) : (
                          "—"
                        )}
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
                          to={`/citizen/applications/${a.id}`}
                          className="btn btn-secondary"
                          style={{ padding: "6px 12px", fontSize: 12 }}
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {Array.isArray(apps) && apps.length > 0 && (
          <div className="pagination">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
            >
              ← Prev
            </button>

            <span className="page-info">
              Showing {offset + 1}–{offset + apps.length}
            </span>

            <button
              disabled={apps.length < LIMIT}
              onClick={() => setOffset(offset + LIMIT)}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80
      ? "var(--success)"
      : pct >= 60
      ? "var(--warning)"
      : "var(--danger)";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          width: 60,
          height: 6,
          background: "var(--border)",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 3,
          }}
        />
      </div>

      <span
        style={{
          fontSize: 12,
          fontFamily: "var(--mono)",
          color: "var(--text2)",
        }}
      >
        {pct}%
      </span>
    </div>
  );
}