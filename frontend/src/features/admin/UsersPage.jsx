import React, { useState, useEffect } from "react";
import { adminApi } from "../../api/admin.api";
import { fmtDate } from "../../utils/formatters";

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const LIMIT = 20;

  useEffect(() => {
    setLoading(true);

    adminApi
      .getUsers({ limit: LIMIT, offset })
      .then((r) => {
        const data = r?.data;

        let list = [];

        if (Array.isArray(data)) list = data;
        else if (Array.isArray(data?.users)) list = data.users;
        else if (Array.isArray(data?.items)) list = data.items;
        else if (Array.isArray(data?.data)) list = data.data;

        setUsers(list);
      })
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [offset]);

  const safeUsers = Array.isArray(users) ? users : [];

  return (
    <div>
      <div className="page-header">
        <h1>User Management</h1>
        <p>All registered users in the system</p>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
        ) : safeUsers.length === 0 ? (
          <div className="empty-state">
            <div className="icon">👥</div>
            <h3>No users found</h3>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>State</th>
                  <th>Joined</th>
                </tr>
              </thead>

              <tbody>
                {safeUsers.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <span
                        style={{
                          fontFamily: "var(--mono)",
                          fontSize: 12,
                          color: "var(--text2)",
                        }}
                      >
                        #{u.id}
                      </span>
                    </td>

                    <td style={{ fontWeight: 600 }}>{u.name || "—"}</td>

                    <td style={{ color: "var(--text2)", fontSize: 13 }}>
                      {u.email}
                    </td>

                    <td>
                      <span className={`role-badge role-${u.role}`}>
                        {u.role?.toUpperCase()}
                      </span>
                    </td>

                    <td style={{ color: "var(--text2)", fontSize: 13 }}>
                      {u.state || "—"}
                    </td>

                    <td style={{ color: "var(--text2)", fontSize: 13 }}>
                      {fmtDate(u.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {safeUsers.length > 0 && (
          <div className="pagination">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
            >
              ← Prev
            </button>

            <span className="page-info">
              {offset + 1}–{offset + safeUsers.length}
            </span>

            <button
              disabled={safeUsers.length < LIMIT}
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