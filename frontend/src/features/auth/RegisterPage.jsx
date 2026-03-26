import React, { useState, useEffect } from "react";
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../api/auth.api';
import { useToast } from '../../app/providers';
import './Auth.css';

export default function RegisterPage() {
  const { addToast } = useToast();
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
      addToast('Account created! Please sign in.', 'success');
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Try again.');
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
        <h2>Register</h2>
        <p className="auth-sub">Fill in your details to get started</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label>Full Name *</label>
              <input required placeholder="Your name" value={form.name} onChange={set('name')} />
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input placeholder="+91 XXXXX XXXXX" value={form.phone} onChange={set('phone')} />
            </div>
          </div>
          <div className="form-group">
            <label>Email Address *</label>
            <input type="email" required placeholder="you@example.com" value={form.email} onChange={set('email')} />
          </div>
          <div className="form-group">
            <label>Password *</label>
            <input type="password" required minLength={6} placeholder="Min 6 characters" value={form.password} onChange={set('password')} />
          </div>
          <div className="form-group">
            <label>State</label>
            <input placeholder="Your state" value={form.state} onChange={set('state')} />
          </div>
          <div className="form-group">
            <label>Address</label>
            <textarea rows={2} placeholder="Your address" value={form.address} onChange={set('address')} style={{ resize: 'vertical' }} />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }} disabled={loading}>
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-link">Already have an account? <Link to="/login">Sign in</Link></p>
      </div>
    </div>
  );
}