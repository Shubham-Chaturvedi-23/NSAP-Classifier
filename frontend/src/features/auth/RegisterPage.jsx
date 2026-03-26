import React, { useState, useEffect } from "react";
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../api/auth.api';
import { useToast } from '../../app/providers';
import { useTranslation } from 'react-i18next';
import './Auth.css';

export default function RegisterPage() {
  const { addToast } = useToast();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '', state: '', address: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await authApi.register(form);
      addToast(t('auth.account_created'), 'success');
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.reg_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <span className="auth-brand-icon">⚖️</span>
        <h1>NSAP</h1>
        <p>Create your citizen account</p>
      </div>

      <div className="auth-card card" style={{ maxWidth: 480 }}>
        <h2>{t('auth.register')}</h2>
        <p className="auth-sub">{t('auth.fill_details')}</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label>{t('auth.full_name')} *</label>
              <input required placeholder={t('auth.your_name')} value={form.name} onChange={set('name')} />
            </div>
            <div className="form-group">
              <label>{t('auth.phone')}</label>
              <input placeholder={t('auth.phone_format')} value={form.phone} onChange={set('phone')} />
            </div>
          </div>
          <div className="form-group">
            <label>{t('auth.email')} *</label>
            <input type="email" required placeholder="you@example.com" value={form.email} onChange={set('email')} />
          </div>
          <div className="form-group">
            <label>{t('auth.password')} *</label>
            <input type="password" required minLength={6} placeholder="Min 6 characters" value={form.password} onChange={set('password')} />
          </div>
          <div className="form-group">
            <label>{t('auth.state')}</label>
            <input placeholder={t('auth.your_state')} value={form.state} onChange={set('state')} />
          </div>
          <div className="form-group">
            <label>{t('auth.address')}</label>
            <textarea rows={2} placeholder={t('auth.your_address')} value={form.address} onChange={set('address')} style={{ resize: 'vertical' }} />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }} disabled={loading}>
            {loading ? t('auth.creating_account') : t('auth.create_account')}
          </button>
        </form>

        <p className="auth-link">{t('auth.already_have_account')} <Link to="/login">{t('auth.sign_in_link')}</Link></p>
      </div>
    </div>
  );
}