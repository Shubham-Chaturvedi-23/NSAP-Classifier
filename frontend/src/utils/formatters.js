export const fmtDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

export const fmtDateTime = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

export const fmtCurrency = (n) => {
  if (n == null) return '—';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
};

export const fmtPercent = (n, dec = 1) => {
  if (n == null) return '—';
  return `${(n * 100).toFixed(dec)}%`;
};

export const getStatusLabel = (s) =>
  ({ pending: 'Pending', auto_approved: 'Auto Approved', needs_review: 'Needs Review', approved: 'Approved', rejected: 'Rejected' }[s] || s);

export const getRequiredDocuments = (formData) => {
  const required = ['aadhaar'];
  if (formData?.bpl_card === 'Yes') required.push('bpl_card');
  if (formData?.marital_status === 'Widowed') required.push('death_certificate');
  if (formData?.has_disability === 'Yes') required.push('disability_certificate');
  return required;
};