import React, { useState, useEffect, useRef } from "react";
import { useParams, Link } from 'react-router-dom';
import { citizenApi } from '../../api/citizen.api';
import { useToast } from '../../app/providers';
import { fmtDateTime, getStatusLabel, getRequiredDocuments } from '../../utils/formatters';
import { STATUS_BADGE_MAP, SCHEME_LABELS, DOC_LABELS } from '../../utils/constants';

const renderValue = (value) => {
  if (value == null || value === '') return '—';
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return '—';
    }
  }
  return String(value);
};

export default function CitizenApplicationDetail() {
  const { id } = useParams();
  const { addToast } = useToast();
  const [app, setApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState({});
  const [verifying, setVerifying] = useState(false);
  const [verifyReport, setVerifyReport] = useState(null);
  const fileRefs = useRef({});

  const load = () => {
    setLoading(true);
    citizenApi.getApplication(id)
      .then((r) => setApp(r.data))
      .catch(() => addToast('Failed to load application.', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleUpload = async (docType) => {
    const file = fileRefs.current[docType]?.files?.[0];
    if (!file) return;
    setUploading((u) => ({ ...u, [docType]: true }));
    const fd = new FormData();
    fd.append('files', file);
    fd.append('declared_doc_type', docType);
    fd.append('application_id', id);
    try {
      const res = await citizenApi.uploadDocument(fd);
      addToast(`${DOC_LABELS[docType]} uploaded!`, 'success');
      
      // Log OCR debug info to browser console for troubleshooting
      if (res?.data?.documents?.[0]?.ocr_debug) {
        console.log(`[OCR Debug - ${docType}]:`, res.data.documents[0].ocr_debug);
      }
      
      load();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Upload failed.', 'error');
    } finally {
      setUploading((u) => ({ ...u, [docType]: false }));
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await citizenApi.verifyDocuments({ application_id: id });
      const report = res?.data || null;
      setVerifyReport(report);

      if (report?.all_verified) {
        addToast('Verification completed.', 'success');
      } else if (Array.isArray(report?.results)) {
        const failed = report.results.filter((r) => r.status !== 'verified');
        addToast(
          failed.length
            ? `Verification failed for: ${failed.map((f) => DOC_LABELS[f.doc_type] || f.doc_type).join(', ')}`
            : (report?.message || 'Verification failed.'),
          'error'
        );
      } else {
        addToast(report?.message || 'Verification failed.', 'error');
      }

      setTimeout(load, 2000);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Verification failed.', 'error');
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (!app) return <div className="alert alert-error">Application not found.</div>;

  const formData = app.form_data || app;
  const requiredDocs = getRequiredDocuments(formData);
  const uploadedDocs = app.documents || [];
  const docMap = {};
  uploadedDocs.forEach((d) => { docMap[d.doc_type] = d; });
  const allVerified = requiredDocs.every((k) => docMap[k]?.verification_status === 'verified');
  const allUploaded = requiredDocs.every((k) => !!docMap[k]);
  const missingDocs = requiredDocs.filter((k) => !docMap[k]);
  const canEdit = app.status === 'pending' && uploadedDocs.length === 0 && !app.prediction && !app.decision;
  const canRunVerify = app.status === 'pending' && allUploaded && !allVerified;

  return (
    <div style={{ maxWidth: 820 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Link to="/citizen/applications" style={{ color: 'var(--text2)', fontSize: 13 }}>← Applications</Link>
        <span style={{ color: 'var(--border)' }}>/</span>
        <span style={{ fontSize: 13, fontFamily: 'var(--mono)', color: 'var(--text2)' }}>#{id}</span>
      </div>

      {/* Header */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 800 }}>Application #{id}</h2>
            <p style={{ color: 'var(--text2)', fontSize: 13, marginTop: 4 }}>Submitted: {fmtDateTime(app.submitted_at || app.created_at)}</p>
            {canEdit && (
              <div style={{ marginTop: 8 }}>
                <Link to={`/citizen/apply?id=${id}`} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}>
                  Edit Application
                </Link>
              </div>
            )}
            {!canEdit && app.status === 'pending' && (
              <p style={{ color: 'var(--text2)', fontSize: 12, marginTop: 8 }}>
                Editing is available only before the first document upload.
              </p>
            )}
          </div>
          <span className={`badge ${STATUS_BADGE_MAP[app.status] || 'badge-pending'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
            {getStatusLabel(app.status)}
          </span>
        </div>
      </div>

      {/* Applicant Profile */}
      {app.applicant && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Applicant Profile</h3>
          <div className="grid-3" style={{ gap: 8 }}>
            {Object.entries(app.applicant).map(([k, v]) => (
              <div key={k} style={{ padding: '10px 12px', background: 'var(--bg3)', borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k.replace(/_/g, ' ')}</div>
                <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2 }}>{renderValue(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prediction */}
      {app.prediction && (
        <div className="card" style={{ marginBottom: 16, borderLeft: '3px solid var(--accent)' }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>AI Prediction</h3>
          <div className="grid-3" style={{ gap: 12 }}>
            <div className="stat-card">
              <div className="label">Predicted Scheme</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent)' }}>
                {SCHEME_LABELS[app.prediction.predicted_scheme] || app.prediction.predicted_scheme}
              </div>
            </div>
            <div className="stat-card">
              <div className="label">Confidence</div>
              <div className="value" style={{ fontSize: 20 }}>{Math.round(app.prediction.confidence_score * 100)}%</div>
            </div>
            <div className="stat-card">
              <div className="label">Needs Manual Review</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: app.prediction.needs_review ? 'var(--warning)' : 'var(--success)' }}>
                {app.prediction.needs_review ? '⚠️ Yes' : '✅ No'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Decision */}
      {app.decision && (
        <div className="card" style={{ marginBottom: 16, borderLeft: `3px solid ${app.decision.decision === 'approved' ? 'var(--success)' : 'var(--danger)'}` }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Officer Decision</h3>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <div><div style={{ fontSize: 12, color: 'var(--text2)' }}>Decision</div>
              <span className={`badge ${app.decision.decision === 'approved' ? 'badge-approved' : 'badge-rejected'}`} style={{ marginTop: 4 }}>
                {app.decision.decision?.toUpperCase()}
              </span>
            </div>
            {app.decision.override_scheme && (
              <div><div style={{ fontSize: 12, color: 'var(--text2)' }}>Assigned Scheme</div>
                <div style={{ fontWeight: 700 }}>{SCHEME_LABELS[app.decision.override_scheme] || app.decision.override_scheme}</div>
              </div>
            )}
            {app.decision.remarks && (
              <div style={{ flex: 1 }}><div style={{ fontSize: 12, color: 'var(--text2)' }}>Remarks</div>
                <div style={{ fontSize: 14, marginTop: 4 }}>{app.decision.remarks}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Document Upload */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Required Documents</h3>
          {!allVerified && app.status === 'pending' && (
            <button
              className="btn btn-info"
              style={{ padding: '6px 14px', fontSize: 13 }}
              onClick={handleVerify}
              disabled={!canRunVerify || verifying}
              title={!allUploaded ? `Upload required documents first: ${missingDocs.map((d) => DOC_LABELS[d]).join(', ')}` : ''}
            >
              {verifying ? 'Verifying…' : '🔍 Run Verification'}
            </button>
          )}
          {allVerified && <span className="badge badge-approved">✅ All Verified</span>}
        </div>

        {!allUploaded && app.status === 'pending' && (
          <div className="alert alert-info" style={{ marginBottom: 12 }}>
            Upload remaining documents to continue: {missingDocs.map((d) => DOC_LABELS[d]).join(', ')}.
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {requiredDocs.map((docType) => {
            const uploaded = docMap[docType];
            const status = uploaded?.verification_status || null;
            const canReplace = app.status === 'pending' && status !== 'verified';
            return (
              <div key={docType} style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 20 }}>{docType === 'aadhaar' ? '🪪' : docType === 'bpl_card' ? '📄' : docType === 'death_certificate' ? '📜' : '♿'}</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{DOC_LABELS[docType]} <span style={{ color: 'var(--danger)', fontSize: 12 }}>*</span></div>
                    {uploaded && <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 2 }}>Uploaded</div>}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {status && (
                    <span className={`badge ${status === 'verified' ? 'badge-approved' : status === 'failed' ? 'badge-rejected' : 'badge-pending'}`}>
                      {status}
                    </span>
                  )}
                  {canReplace ? (
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        type="file" accept=".pdf,.jpg,.jpeg,.png"
                        ref={(el) => { fileRefs.current[docType] = el; }}
                        style={{ fontSize: 12, width: 'auto' }}
                      />
                      <button
                        className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}
                        onClick={() => handleUpload(docType)}
                        disabled={uploading[docType]}
                      >
                        {uploading[docType] ? 'Uploading…' : uploaded ? '♻️ Replace' : '⬆️ Upload'}
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>

        {allVerified && app.status === 'pending' && (
          <div className="alert alert-success" style={{ marginTop: 16 }}>
            ✅ All documents verified. Your application is ready for officer review.
          </div>
        )}

        {verifyReport && Array.isArray(verifyReport.results) && (
          <div style={{ marginTop: 14 }}>
            <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Latest Verification Report
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {verifyReport.results.map((r) => {
                const ok = r.status === 'verified';
                return (
                  <div
                    key={`${r.doc_type}-${r.document_id || r.certificate_number || Math.random()}`}
                    style={{
                      border: `1px solid ${ok ? 'var(--success)' : 'var(--danger)'}`,
                      background: ok ? 'rgba(29,185,84,0.08)' : 'rgba(229,57,53,0.08)',
                      borderRadius: 8,
                      padding: '10px 12px'
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>
                      {DOC_LABELS[r.doc_type] || r.doc_type} - {ok ? 'Verified' : 'Failed'}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text2)' }}>{r.message || 'No details provided.'}</div>
                    {r.certificate_number && (
                      <div style={{ fontSize: 12, marginTop: 4 }}>
                        Certificate: <span style={{ fontFamily: 'var(--mono)' }}>{r.certificate_number}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Form Data */}
      <div className="card">
        <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Application Data</h3>
        <div className="grid-3" style={{ gap: 8 }}>
          {Object.entries(formData).filter(([k]) => !['id','status','created_at','updated_at','prediction','decision','documents','form_data','applicant'].includes(k)).map(([k, v]) => (
            <div key={k} style={{ padding: '10px 12px', background: 'var(--bg3)', borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k.replace(/_/g, ' ')}</div>
              <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2 }}>{renderValue(v)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}