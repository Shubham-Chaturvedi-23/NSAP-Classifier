import React, { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 40,
          background: 'var(--bg)',
        }}>
          <div style={{ maxWidth: 480, textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
            <h2 style={{ color: 'var(--text)', fontSize: 20, fontWeight: 800, marginBottom: 8 }}>
              Something went wrong
            </h2>
            <p style={{ color: 'var(--text2)', fontSize: 14, marginBottom: 24, lineHeight: 1.6 }}>
              An unexpected error occurred. Please refresh the page or contact support if the problem persists.
            </p>
            <div style={{
              background: 'var(--bg2)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '12px 16px',
              marginBottom: 24,
              textAlign: 'left',
              fontFamily: 'var(--mono)',
              fontSize: 12,
              color: 'var(--danger)',
              wordBreak: 'break-all',
            }}>
              {this.state.error?.message || 'Unknown error'}
            </div>
            <button
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              🔄 Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}