import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { officerApi } from '../../api/officer.api';
import { useToast } from '../../app/providers';
import { fmtDateTime, getStatusLabel } from '../../utils/formatters';
import { STATUS_BADGE_MAP, SCHEME_LABELS, DOC_LABELS } from '../../utils/constants';

export default function OfficerReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();
  const [app, setApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [remarks, setRemarks] = useState('');
  const [overrideScheme, setOverrideScheme] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    officerApi.getApplication(id)
      .then((r) => {
        setApp(r.data);
        if (r.data?.prediction?.predicted_scheme) {
          setOverrideScheme(r.data.prediction.predicted_scheme);
        }
      })
      .catch(() => addToast('Failed to load application.', 'error'))
      .finally(() => setLoading(false));
  }, [id]);

  const canDecide = app && !app.decision && ['needs_review', 'auto_approved'].includes(app.status);
  const isReadOnlyView = location.pathname.endsWith('/view');

  const handleDecide = async (e) => {
    e.preventDefault();
    if (!remarks.trim()) { addToast('Remarks are required.', 'error'); return; }
    if (!overrideScheme) { addToast('Please select final scheme.', 'error'); return; }

    const decision = overrideScheme === 'NOT_ELIGIBLE' ? 'rejected' : 'approved';

    setSubmitting(true);
    try {
      await officerApi.decide(id, {
        decision,
        remarks,
        override_scheme: overrideScheme,
      });
      addToast('Decision submitted!', 'success');
      navigate('/officer/queue');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Submission failed.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (!app) return <div className="alert alert-error">Application not found.</div>;

  const formData = app.form_data || app;

  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Link to="/officer/queue" style={{ color: 'var(--text2)', fontSize: 13 }}>← Queue</Link>
        <span style={{ color: 'var(--border)' }}>/</span>
        <span style={{ fontSize: 13, fontFamily: 'var(--mono)', color: 'var(--text2)' }}>Review #{id}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 16, alignItems: 'start' }}>

        {/* Left column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Status header */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
            <div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text2)' }}>Application #{id}</div>
              <div style={{ fontSize: 13, color: 'var(--text2)', marginTop: 2 }}>Submitted: {fmtDateTime(app.created_at)}</div>
            </div>
            <span className={`badge ${STATUS_BADGE_MAP[app.status] || 'badge-pending'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
              {getStatusLabel(app.status)}
            </span>
          </div>

          {/* AI Prediction + SHAP */}
          {app.prediction && (
            <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
              <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>
                🤖 AI Prediction
              </h3>
              <div className="grid-3" style={{ gap: 12, marginBottom: 16 }}>
                <div className="stat-card">
                  <div className="label">Predicted Scheme</div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--accent)' }}>
                    {SCHEME_LABELS[app.prediction.predicted_scheme] || app.prediction.predicted_scheme}
                  </div>
                </div>
                <div className="stat-card">
                  <div className="label">Confidence</div>
                  <div className="value" style={{ fontSize: 22 }}>{Math.round(app.prediction.confidence_score * 100)}%</div>
                </div>
                <div className="stat-card">
                  <div className="label">Needs Review</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: app.prediction.needs_review ? 'var(--warning)' : 'var(--success)' }}>
                    {app.prediction.needs_review ? '⚠️ Yes' : '✅ No'}
                  </div>
                </div>
              </div>

              {/* Probability breakdown */}
              {app.prediction.all_probabilities && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
                    Scheme Probabilities
                  </div>
                  {Object.entries(app.prediction.all_probabilities).map(([scheme, prob]) => {
                    const pct = Math.round(prob * 100);
                    return (
                      <div key={scheme} style={{ marginBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                          <span>{SCHEME_LABELS[scheme] || scheme}</span>
                          <span style={{ fontFamily: 'var(--mono)' }}>{pct}%</span>
                        </div>
                        <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${pct}%`, height: '100%', background: scheme === app.prediction.predicted_scheme ? 'var(--accent)' : 'var(--text2)', borderRadius: 3, transition: 'width 0.5s' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* SHAP */}
              {app.prediction.shap_explanation ? (
                <div style={{ marginTop: 16, padding: 14, background: 'var(--bg3)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
                    🔍 SHAP Explanation (Top Factors)
                  </div>
                  {(() => {
                    const MIN_IMPACT = 0.01;
                    const strongFactors = Object.entries(app.prediction.shap_explanation)
                      .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                      .filter(([, val]) => Math.abs(val) >= MIN_IMPACT)
                      .slice(0, 8);

                    if (!strongFactors.length) {
                      return (
                        <div style={{ color: 'var(--text2)', fontSize: 12 }}>
                          No strong feature drivers for this prediction (all SHAP impacts are near zero).
                        </div>
                      );
                    }

                    return strongFactors.map(([feat, val]) => {
                      const abs = Math.abs(val);
                      const max = 0.5;
                      const pct = Math.min(100, Math.round((abs / max) * 100));
                      return (
                        <div key={feat} style={{ marginBottom: 6 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 2 }}>
                            <span style={{ color: 'var(--text2)' }}>{feat.replace(/_/g, ' ')}</span>
                            <span style={{ fontFamily: 'var(--mono)', color: val > 0 ? 'var(--success)' : 'var(--danger)' }}>
                              {val > 0 ? '+' : ''}{val.toFixed(3)}
                            </span>
                          </div>
                          <div style={{ height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                            <div style={{ width: `${pct}%`, height: '100%', background: val > 0 ? 'var(--success)' : 'var(--danger)', borderRadius: 2 }} />
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              ) : (
                <div style={{ marginTop: 16, padding: 14, background: 'var(--bg3)', borderRadius: 8, color: 'var(--text2)', fontSize: 12 }}>
                  SHAP explanation not available for this prediction.
                </div>
              )}
            </div>
          )}

          {/* Applicant form data */}
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>
              📋 Applicant Data
            </h3>
            <div className="grid-3" style={{ gap: 8 }}>
              {Object.entries(formData)
                .filter(([k]) => !['id','status','created_at','updated_at','prediction','decision','documents','form_data'].includes(k))
                .map(([k, v]) => (
                  <div key={k} style={{ padding: '10px 12px', background: 'var(--bg3)', borderRadius: 6 }}>
                    <div style={{ fontSize: 10, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k.replace(/_/g, ' ')}</div>
                    <div style={{ fontWeight: 600, fontSize: 13, marginTop: 2 }}>{String(v)}</div>
                  </div>
                ))}
            </div>
          </div>

          {/* Documents */}
          {app.documents?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>
                📄 Documents
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {app.documents.map((doc) => (
                  <div key={doc.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg3)', borderRadius: 8 }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{DOC_LABELS[doc.doc_type] || doc.doc_type}</div>
                      {doc.certificate_number && <div style={{ fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>Cert: {doc.certificate_number}</div>}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className={`badge ${doc.verification_status === 'verified' ? 'badge-approved' : doc.verification_status === 'failed' ? 'badge-rejected' : 'badge-pending'}`}>
                        {doc.verification_status || 'pending'}
                      </span>
                      {doc.file_url && (
                        <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}>
                          View
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column: Decision panel */}
        {!isReadOnlyView && (
        <div style={{ position: 'sticky', top: 80 }}>
          <div className="card" style={{ borderTop: '3px solid var(--accent2)' }}>
            <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>⚖️ Decision Panel</h3>

            {app.decision ? (
              <div>
                <div className="alert alert-info" style={{ marginBottom: 0 }}>
                  Decision already recorded on {fmtDateTime(app.decision.decided_at)}.
                </div>
                <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div><span style={{ fontSize: 11, color: 'var(--text2)' }}>DECISION</span>
                    <div><span className={`badge ${app.decision.decision === 'approved' ? 'badge-approved' : 'badge-rejected'}`} style={{ marginTop: 4 }}>{app.decision.decision?.toUpperCase()}</span></div>
                  </div>
                  {app.decision.override_scheme && <div><span style={{ fontSize: 11, color: 'var(--text2)' }}>ASSIGNED SCHEME</span><div style={{ fontWeight: 700 }}>{SCHEME_LABELS[app.decision.override_scheme] || app.decision.override_scheme}</div></div>}
                  {app.decision.remarks && <div><span style={{ fontSize: 11, color: 'var(--text2)' }}>REMARKS</span><div style={{ fontSize: 13, marginTop: 2 }}>{app.decision.remarks}</div></div>}
                </div>
              </div>
            ) : !canDecide ? (
              <div className="alert alert-info">This application is not in a reviewable state.</div>
            ) : (
              <form onSubmit={handleDecide}>
                <div className="form-group">
                  <label>Final Scheme *</label>
                  <select value={overrideScheme} onChange={(e) => setOverrideScheme(e.target.value)}>
                    <option value="">Select scheme</option>
                    {Object.entries(SCHEME_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                  <span style={{ fontSize: 11, color: 'var(--text2)' }}>
                    Choosing Not Eligible will reject the application.
                  </span>
                </div>

                <div className="form-group">
                  <label>Remarks *</label>
                  <textarea
                    rows={4} required
                    placeholder="Provide clear reasoning for your decision…"
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    style={{ resize: 'vertical' }}
                  />
                </div>

                <button
                  type="submit"
                  className={`btn ${overrideScheme === 'NOT_ELIGIBLE' ? 'btn-danger' : 'btn-success'}`}
                  style={{ width: '100%', justifyContent: 'center' }}
                  disabled={submitting}
                >
                  {submitting ? 'Submitting…' : overrideScheme === 'NOT_ELIGIBLE' ? 'Submit Rejection' : 'Submit Approval'}
                </button>
              </form>
            )}
          </div>
        </div>
        )}
      </div>
    </div>
  );
}