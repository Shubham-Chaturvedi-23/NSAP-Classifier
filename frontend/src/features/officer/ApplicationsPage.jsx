import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { officerApi } from "../../api/officer.api";
import { fmtDate, getStatusLabel } from "../../utils/formatters";
import { STATUS_BADGE_MAP, SCHEME_LABELS } from "../../utils/constants";

export default function OfficerApplicationsPage() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const LIMIT = 20;

  useEffect(() => {
    setLoading(true);

    officerApi
      .getApplications({ limit: LIMIT, offset })
      .then((res) => {
        const data = res?.data;

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

  const safeApps = Array.isArray(apps) ? apps : [];

  return (
    <div>
      <div className="page-header">
        <h1>All Applications</h1>
        <p>Browse and review all assigned applications</p>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
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
                  <th>Scheme</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {safeApps.map((a) => (
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

                    <td>{fmtDate(a.submitted_at || a.created_at)}</td>

                    <td>{a.citizen_name || a.citizen_email || "—"}</td>

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
                        ? `${Math.round(
                            (a?.prediction?.confidence_score ?? a?.confidence_score) * 100
                          )}%`
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
                        to={`/officer/applications/${a.id}/view`}
                        className="btn btn-secondary"
                        style={{ padding: "6px 14px", fontSize: 12 }}
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

        {safeApps.length > 0 && (
          <div className="pagination">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
            >
              ← Prev
            </button>

            <span className="page-info">
              {offset + 1}–{offset + safeApps.length}
            </span>

            <button
              disabled={safeApps.length < LIMIT}
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