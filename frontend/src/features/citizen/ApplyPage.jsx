import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from 'react-router-dom';
import { citizenApi } from '../../api/citizen.api';
import { useToast } from '../../app/providers';
import {
  GENDER_OPTIONS, MARITAL_OPTIONS, AREA_OPTIONS, YES_NO,
  EMPLOYMENT_OPTIONS, SOCIAL_CATEGORIES, DISABILITY_TYPES, INDIA_STATES
} from '../../utils/constants';

const FIELDS = [
  { key: 'age', label: 'Age', type: 'number', min: 18, max: 120, placeholder: 'e.g. 65' },
  { key: 'gender', label: 'Gender', type: 'select', options: GENDER_OPTIONS },
  { key: 'marital_status', label: 'Marital Status', type: 'select', options: MARITAL_OPTIONS },
  { key: 'annual_income', label: 'Annual Income (₹)', type: 'number', min: 0, placeholder: 'e.g. 35000' },
  { key: 'bpl_card', label: 'BPL Card Holder?', type: 'select', options: YES_NO },
  { key: 'area_type', label: 'Area Type', type: 'select', options: AREA_OPTIONS },
  { key: 'state', label: 'State', type: 'select', options: INDIA_STATES },
  { key: 'social_category', label: 'Social Category', type: 'select', options: SOCIAL_CATEGORIES },
  { key: 'employment_status', label: 'Employment Status', type: 'select', options: EMPLOYMENT_OPTIONS },
  { key: 'has_disability', label: 'Has Disability?', type: 'select', options: YES_NO },
  { key: 'disability_percentage', label: 'Disability Percentage', type: 'number', min: 0, max: 100, placeholder: '0-100' },
  { key: 'disability_type', label: 'Disability Type', type: 'select', options: DISABILITY_TYPES },
  { key: 'aadhaar_linked', label: 'Aadhaar Linked?', type: 'select', options: YES_NO },
  { key: 'bank_account', label: 'Bank Account?', type: 'select', options: YES_NO },
];

const DEFAULTS = {
  age: '', gender: 'Male', marital_status: 'Single', annual_income: '',
  bpl_card: 'No', area_type: 'Rural', state: 'Gujarat', social_category: 'General',
  employment_status: 'Unemployed', has_disability: 'No',
  disability_percentage: 0, disability_type: 'None',
  aadhaar_linked: 'Yes', bank_account: 'Yes',
};

export default function ApplyPage() {
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState(DEFAULTS);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.value;
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((er) => ({ ...er, [k]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.age || form.age < 18 || form.age > 120) e.age = 'Age must be 18–120';
    if (!form.annual_income && form.annual_income !== 0) e.annual_income = 'Income is required';
    if (form.has_disability === 'Yes' && (form.disability_percentage < 1 || form.disability_percentage > 100))
      e.disability_percentage = 'Enter valid percentage';
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    try {
      const payload = {
        ...form,
        age: Number(form.age),
        annual_income: Number(form.annual_income),
        disability_percentage: Number(form.disability_percentage),
      };
      const res = await citizenApi.apply(payload);
      addToast('Application submitted!', 'success');
      navigate(`/citizen/applications/${res.data.id || res.data.application_id}`);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Submission failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-header">
        <h1>New Application</h1>
        <p>Submit your details for scheme eligibility assessment</p>
      </div>

      <div className="card">
        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          ℹ️ Fill all fields accurately. The prediction model uses this data to recommend the appropriate scheme.
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Personal Information</h3>
            <div className="grid-2">
              {FIELDS.slice(0, 4).map((f) => (
                <FieldInput key={f.key} field={f} value={form[f.key]} onChange={set(f.key)} error={errors[f.key]} />
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Socio-Economic Details</h3>
            <div className="grid-2">
              {FIELDS.slice(4, 9).map((f) => (
                <FieldInput key={f.key} field={f} value={form[f.key]} onChange={set(f.key)} error={errors[f.key]} />
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Disability & Documentation</h3>
            <div className="grid-2">
              {FIELDS.slice(9).map((f) => (
                <FieldInput key={f.key} field={f} value={form[f.key]} onChange={set(f.key)} error={errors[f.key]}
                  disabled={f.key === 'disability_percentage' || f.key === 'disability_type' ? form.has_disability !== 'Yes' : false}
                />
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Submitting…' : '🚀 Submit Application'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/citizen/applications')}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FieldInput({ field, value, onChange, error, disabled }) {
  return (
    <div className="form-group">
      <label>{field.label}</label>
      {field.type === 'select' ? (
        <select value={value} onChange={onChange} disabled={disabled}>
          {field.options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input
          type={field.type}
          value={value}
          onChange={onChange}
          min={field.min}
          max={field.max}
          placeholder={field.placeholder}
          disabled={disabled}
          style={disabled ? { opacity: 0.4 } : {}}
        />
      )}
      {error && <span className="error">{error}</span>}
    </div>
  );
}