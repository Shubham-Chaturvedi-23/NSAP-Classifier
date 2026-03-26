import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from 'react-router-dom';
import { citizenApi } from '../../api/citizen.api';
import { useToast } from '../../app/providers';
import { useTranslation } from 'react-i18next';
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
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('id');
  const [form, setForm] = useState(DEFAULTS);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.value;
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((er) => ({ ...er, [k]: '' }));
  };

  const { t } = useTranslation();

  useEffect(() => {
    if (!editId) return;
    setLoading(true);
    citizenApi.getApplication(editId)
      .then((res) => {
        const app = res?.data || {};
        setForm((prev) => ({
          ...prev,
          age: app.age ?? prev.age,
          gender: app.gender ?? prev.gender,
          marital_status: app.marital_status ?? prev.marital_status,
          annual_income: app.annual_income ?? prev.annual_income,
          bpl_card: app.bpl_card ?? prev.bpl_card,
          area_type: app.area_type ?? prev.area_type,
          state: app.state ?? prev.state,
          social_category: app.social_category ?? prev.social_category,
          employment_status: app.employment_status ?? prev.employment_status,
          has_disability: app.has_disability ?? prev.has_disability,
          disability_percentage: app.disability_percentage ?? prev.disability_percentage,
          disability_type: app.disability_type ?? prev.disability_type,
          aadhaar_linked: app.aadhaar_linked ?? prev.aadhaar_linked,
          bank_account: app.bank_account ?? prev.bank_account,
        }));
      })
      .catch(() => addToast('Failed to load application for edit.', 'error'))
      .finally(() => setLoading(false));
  }, [editId]);
  
  const validate = () => {
    const e = {};
    if (!form.age || form.age < 18 || form.age > 120) e.age = t('app.age_invalid');
    if (!form.annual_income && form.annual_income !== 0) e.annual_income = t('app.income_required');
    if (form.has_disability === 'Yes' && (form.disability_percentage < 1 || form.disability_percentage > 100))
      e.disability_percentage = t('app.percentage_invalid');
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
      const res = editId
        ? await citizenApi.updateApplication(editId, payload)
        : await citizenApi.apply(payload);
      addToast(editId ? 'Application updated.' : t('app.submitted'), 'success');
      navigate(`/citizen/applications/${res.data.id || res.data.application_id || editId}`);
    } catch (err) {
      addToast(err.response?.data?.detail || t('app.submission_failed'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-header">
        <h1>{editId ? 'Edit Application' : t('app.new_application')}</h1>
        <p>{editId ? 'Update details before uploading documents.' : t('app.submit_details')}</p>
      </div>

      <div className="card">
        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          ℹ️ {t('app.fill_accurately')}
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>{t('app.personal_info')}</h3>
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
                  disabled={
                    (f.key === 'disability_percentage' || f.key === 'disability_type')
                      ? String(form.has_disability).toLowerCase() !== 'yes'
                      : false
                  }
                />
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving…' : (editId ? '💾 Save Changes' : '🚀 Submit Application')}
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