export const ROLES = { CITIZEN: 'citizen', OFFICER: 'officer', ADMIN: 'admin' };

export const APPLICATION_STATUS = {
  PENDING: 'pending',
  AUTO_APPROVED: 'auto_approved',
  NEEDS_REVIEW: 'needs_review',
  APPROVED: 'approved',
  REJECTED: 'rejected',
};

export const SCHEMES = { OAP: 'OAP', WP: 'WP', DP: 'DP', NOT_ELIGIBLE: 'NOT_ELIGIBLE' };

export const SCHEME_LABELS = {
  OAP: 'Old Age Pension',
  WP: 'Widow Pension',
  DP: 'Disability Pension',
  NOT_ELIGIBLE: 'Not Eligible',
};

export const STATUS_BADGE_MAP = {
  pending: 'badge-pending',
  auto_approved: 'badge-auto',
  needs_review: 'badge-review',
  approved: 'badge-approved',
  rejected: 'badge-rejected',
};

export const GENDER_OPTIONS = ['Male', 'Female', 'Other'];
export const MARITAL_OPTIONS = ['Single', 'Married', 'Widowed', 'Divorced', 'Separated'];
export const AREA_OPTIONS = ['Rural', 'Urban'];
export const YES_NO = ['Yes', 'No'];
export const EMPLOYMENT_OPTIONS = ['Employed', 'Unemployed', 'Self-employed', 'Retired'];
export const SOCIAL_CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS'];
export const DISABILITY_TYPES = ['Visual', 'Hearing', 'Physical', 'Intellectual', 'Mental', 'Multiple', 'None'];

export const INDIA_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat',
  'Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh',
  'Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab',
  'Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh',
  'Uttarakhand','West Bengal','Delhi','Jammu and Kashmir','Ladakh',
];

export const DOC_LABELS = {
  aadhaar: 'Aadhaar Card',
  bpl_card: 'BPL Card',
  death_certificate: 'Death Certificate',
  disability_certificate: 'Disability Certificate',
};