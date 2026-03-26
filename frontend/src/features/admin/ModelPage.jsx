import React, { useState, useEffect } from "react";
import { adminApi } from '../../api/admin.api';

export default function AdminModelPage() {
  const [metrics, setMetrics] = useState(null);
  const [fairness, setFairness] = useState([]);
  const [loading, setLoading] = useState(true);
  const confusionUrl = adminApi.getConfusionMatrix();
  const shapUrl = adminApi.getShapSummary();

  useEffect(() => {
    Promise.all([adminApi.getModelMetrics(), adminApi.getFairnessReport()])
      .then(([m, f]) => {
        setMetrics(m.data);
        setFairness(f.data?.groups || f.data || []);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <h1>Model Metrics</h1>
        <p>CatBoost prediction model performance and fairness</p>
      </div>

      {/* Key metrics */}
      {metrics && (
        <div className="grid-4" style={{ marginBottom: 24 }}>
          {[
            { label: 'Accuracy', value: metrics.accuracy != null ? `${(metrics.accuracy * 100).toFixed(1)}%` : '—' },
            { label: 'Precision', value: metrics.precision != null ? `${(metrics.precision * 100).toFixed(1)}%` : '—' },
            { label: 'Recall', value: metrics.recall != null ? `${(metrics.recall * 100).toFixed(1)}%` : '—' },
            { label: 'F1 Score', value: metrics.f1_score != null ? `${(metrics.f1_score * 100).toFixed(1)}%` : '—' },
          ].map((m) => (
            <div key={m.label} className="card stat-card">
              <div className="label">{m.label}</div>
              <div className="value">{m.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Per-class metrics */}
      {metrics?.per_class && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Per-Class Metrics</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Scheme</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr>
              </thead>
              <tbody>
                {Object.entries(metrics.per_class).map(([scheme, vals]) => (
                  <tr key={scheme}>
                    <td style={{ fontWeight: 700 }}>{scheme}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{vals.precision != null ? `${(vals.precision * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{vals.recall != null ? `${(vals.recall * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{vals.f1_score != null ? `${(vals.f1_score * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)', color: 'var(--text2)' }}>{vals.support ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fairness report */}
      {fairness.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>
            ⚖️ Fairness Report
          </h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Group</th><th>Category</th><th>Accuracy</th><th>Approval Rate</th><th>Flag</th></tr>
              </thead>
              <tbody>
                {fairness.map((g, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{g.group || g.name || '—'}</td>
                    <td style={{ color: 'var(--text2)' }}>{g.category || '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{g.accuracy != null ? `${(g.accuracy * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{g.approval_rate != null ? `${(g.approval_rate * 100).toFixed(1)}%` : '—'}</td>
                    <td>
                      {g.flag
                        ? <span className="badge badge-rejected">⚠️ Flagged</span>
                        : <span className="badge badge-approved">✓ OK</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Visual charts from backend */}
      <div className="grid-2">
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>Confusion Matrix</h3>
          <img
            src={confusionUrl}
            alt="Confusion Matrix"
            style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }}
          />
          <div style={{ display: 'none', color: 'var(--text2)', fontSize: 13, textAlign: 'center', padding: 20 }}>Chart not available</div>
        </div>
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>SHAP Feature Importance</h3>
          <img
            src={shapUrl}
            alt="SHAP Summary"
            style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }}
          />
          <div style={{ display: 'none', color: 'var(--text2)', fontSize: 13, textAlign: 'center', padding: 20 }}>Chart not available</div>
        </div>
      </div>
    </div>
  );
}