import React, { useState, useEffect } from "react";
import { adminApi } from '../../api/admin.api';

export default function AdminModelPage() {
  const [metrics, setMetrics] = useState(null);
  const [fairness, setFairness] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confusionUrl, setConfusionUrl] = useState('');
  const [shapUrl, setShapUrl] = useState('');
  const [confusionError, setConfusionError] = useState(false);
  const [shapError, setShapError] = useState(false);

  useEffect(() => {
    Promise.all([adminApi.getModelMetrics(), adminApi.getFairnessReport()])
      .then(([m, f]) => {
        const metricsPayload = m.data || {};
        setMetrics(metricsPayload.best_model || metricsPayload);

        const fairnessPayload = f.data || {};
        setFairness(
          fairnessPayload.all_groups ||
          fairnessPayload.groups ||
          fairnessPayload.data ||
          []
        );
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let confusionObjectUrl;
    let shapObjectUrl;

    Promise.allSettled([
      adminApi.getConfusionMatrixBlob(),
      adminApi.getShapSummaryBlob(),
    ]).then(([confusionRes, shapRes]) => {
      if (confusionRes.status === 'fulfilled' && confusionRes.value?.data) {
        confusionObjectUrl = URL.createObjectURL(confusionRes.value.data);
        setConfusionUrl(confusionObjectUrl);
      } else {
        setConfusionError(true);
      }

      if (shapRes.status === 'fulfilled' && shapRes.value?.data) {
        shapObjectUrl = URL.createObjectURL(shapRes.value.data);
        setShapUrl(shapObjectUrl);
      } else {
        setShapError(true);
      }
    });

    return () => {
      if (confusionObjectUrl) URL.revokeObjectURL(confusionObjectUrl);
      if (shapObjectUrl) URL.revokeObjectURL(shapObjectUrl);
    };
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
            { label: 'F1 Score', value: metrics.f1_weighted != null ? `${(metrics.f1_weighted * 100).toFixed(1)}%` : '—' },
          ].map((m) => (
            <div key={m.label} className="card stat-card">
              <div className="label">{m.label}</div>
              <div className="value">{m.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Scheme-wise F1 metrics */}
      {metrics && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Scheme-wise F1</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Scheme</th><th>F1 Score</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 700 }}>OAP</td>
                  <td style={{ fontFamily: 'var(--mono)' }}>{metrics.f1_oap != null ? `${(metrics.f1_oap * 100).toFixed(1)}%` : '—'}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700 }}>WP</td>
                  <td style={{ fontFamily: 'var(--mono)' }}>{metrics.f1_wp != null ? `${(metrics.f1_wp * 100).toFixed(1)}%` : '—'}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700 }}>DP</td>
                  <td style={{ fontFamily: 'var(--mono)' }}>{metrics.f1_dp != null ? `${(metrics.f1_dp * 100).toFixed(1)}%` : '—'}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 700 }}>Not Eligible</td>
                  <td style={{ fontFamily: 'var(--mono)' }}>{metrics.f1_not_eligible != null ? `${(metrics.f1_not_eligible * 100).toFixed(1)}%` : '—'}</td>
                </tr>
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
                <tr><th>Dimension</th><th>Group</th><th>Count</th><th>Error Rate</th><th>False Denial</th><th>False Approval</th><th>Flag</th></tr>
              </thead>
              <tbody>
                {fairness.map((g, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{g.group_column || g.dimension || '—'}</td>
                    <td style={{ color: 'var(--text2)' }}>{g.group || g.name || '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{g.count ?? '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{g.error_rate != null ? `${(g.error_rate * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{g.false_not_eligible_rate != null ? `${(g.false_not_eligible_rate * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>{g.false_eligible_rate != null ? `${(g.false_eligible_rate * 100).toFixed(1)}%` : '—'}</td>
                    <td>
                      {String(g.flag || '').replace(/\s+/g, ' ').trim().toUpperCase().includes('OK')
                        ? <span className="badge badge-approved">✓ OK</span>
                        : <span className="badge badge-rejected">⚠️ Flagged</span>}
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
          {confusionUrl && !confusionError ? (
            <img
              src={confusionUrl}
              alt="Confusion Matrix"
              style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
              onError={() => setConfusionError(true)}
            />
          ) : (
            <div style={{ color: 'var(--text2)', fontSize: 13, textAlign: 'center', padding: 20 }}>Chart not available</div>
          )}
        </div>
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>SHAP Feature Importance</h3>
          {shapUrl && !shapError ? (
            <img
              src={shapUrl}
              alt="SHAP Summary"
              style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
              onError={() => setShapError(true)}
            />
          ) : (
            <div style={{ color: 'var(--text2)', fontSize: 13, textAlign: 'center', padding: 20 }}>Chart not available</div>
          )}
        </div>
      </div>
    </div>
  );
}