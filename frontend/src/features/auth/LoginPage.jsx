import React, { useState, useEffect } from "react";
import { Link, useNavigate } from 'react-router-dom';
import { useAuth, useToast } from '../../app/providers';
import { useTranslation } from 'react-i18next';
import { getRoleHomePath } from '../../utils/guards';
import './Auth.css';

export default function LoginPage() {
  const { login } = useAuth();
  const { addToast } = useToast();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const user = await login(form.email, form.password);
      addToast(t('auth.welcome_back'), 'success');
      navigate(getRoleHomePath(user.role));
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.invalid_creds'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <span className="auth-brand-icon">⚖️</span>
        <h1>NSAP</h1>
        <p>National Social Assistance Programme</p>
      </div>

      <div className="auth-card card">
        <h2>{t('auth.login')}</h2>
        <p className="auth-sub">{t('auth.access_portal')}</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('auth.email')}</label>
            <input
              type="email" required placeholder="you@example.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>{t('auth.password')}</label>
            <input
              type="password" required placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }} disabled={loading}>
            {loading ? t('auth.signing_in') : t('auth.login')}
          </button>
        </form>

        <p className="auth-link">{t('auth.no_account')} <Link to="/register">{t('auth.register_here')}</Link></p>

        
      </div>
    </div>
  );
}