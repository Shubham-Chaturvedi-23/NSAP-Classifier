import React, { useState, useEffect } from "react";
import { STATUS_BADGE_MAP, SCHEME_LABELS } from '../../utils/constants';
import { getStatusLabel } from '../../utils/formatters';

// ── Status Badge ──────────────────────────────────────────────
export function StatusBadge({ status, size = 'sm' }) {
  const cls = STATUS_BADGE_MAP[status] || 'badge-pending';
  return (
    <span
      className={`badge ${cls}`}
      style={size === 'lg' ? { fontSize: 13, padding: '6px 14px' } : {}}
    >
      {getStatusLabel(status)}
    </span>
  );
}

// ── Scheme Badge ──────────────────────────────────────────────
export function SchemeBadge({ scheme }) {
  if (!scheme) return <span style={{ color: 'var(--text2)' }}>—</span>;
  const colors = {
    OAP: 'var(--info)',
    WP:  'var(--accent)',
    DP:  'var(--warning)',
    NOT_ELIGIBLE: 'var(--danger)',
  };
  return (
    <span style={{
      fontWeight: 700,
      color: colors[scheme] || 'var(--text)',
      fontSize: 13,
    }}>
      {SCHEME_LABELS[scheme] || scheme}
    </span>
  );
}

// ── Confidence Bar ─────────────────────────────────────────────
export function ConfidenceBar({ value, showLabel = true }) {
  const pct = Math.round((value ?? 0) * 100);
  const color = pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 64, height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden', flexShrink: 0 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.4s ease' }} />
      </div>
      {showLabel && (
        <span style={{ fontSize: 12, fontFamily: 'var(--mono)', color: 'var(--text2)', minWidth: 32 }}>{pct}%</span>
      )}
    </div>
  );
}

// ── Spinner ────────────────────────────────────────────────────
export function Spinner({ size = 36 }) {
  return (
    <div className="loading">
      <div className="spinner" style={{ width: size, height: size }} />
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────
export function EmptyState({ icon = '📭', title = 'Nothing here', description, action }) {
  return (
    <div className="empty-state">
      <div className="icon">{icon}</div>
      <h3>{title}</h3>
      {description && <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text2)' }}>{description}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}

// ── Stat Card ──────────────────────────────────────────────────
export function StatCard({ label, value, icon, color, sub }) {
  return (
    <div className="card stat-card">
      <div className="label" style={color ? { color } : {}}>
        {icon && <span style={{ marginRight: 6 }}>{icon}</span>}{label}
      </div>
      <div className="value">{value ?? '—'}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

// ── Error Alert ────────────────────────────────────────────────
export function ErrorAlert({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="alert alert-error" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span>⚠️ {message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{ background: 'none', border: '1px solid rgba(248,81,73,0.4)', borderRadius: 6, color: '#ff7b72', padding: '4px 10px', fontSize: 12, cursor: 'pointer' }}
        >
          Retry
        </button>
      )}
    </div>
  );
}

// ── Pagination ─────────────────────────────────────────────────
export function Pagination({ offset, count, limit, onPrev, onNext }) {
  return (
    <div className="pagination">
      <button disabled={offset === 0} onClick={onPrev}>← Prev</button>
      <span className="page-info">
        {count === 0 ? 'No results' : `${offset + 1}–${offset + count}`}
      </span>
      <button disabled={count < limit} onClick={onNext}>Next →</button>
    </div>
  );
}

// ── Section Header ──────────────────────────────────────────────
export function SectionHeader({ children }) {
  return (
    <div style={{
      fontSize: 11,
      fontWeight: 700,
      color: 'var(--text2)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      marginBottom: 14,
    }}>
      {children}
    </div>
  );
}