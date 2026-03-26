# NSAP Scheme Classification System — Frontend

React + Vite frontend for the National Social Assistance Programme (NSAP) scheme classification system.

---

## Prerequisites

- Node.js 18+
- npm 9+
- Backend running at `http://localhost:8000`

---

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Copy env file and set your backend URL
cp .env.example .env
# Edit .env if backend runs on a different port

# 3. Start the dev server
npm run dev

# Opens at http://localhost:5173
```

---

## Project Structure

```
src/
├── main.jsx                  # Entry point — mounts React, wires providers
├── styles/globals.css        # Global design tokens + utility classes
│
├── app/
│   ├── providers.jsx         # AuthContext (login/logout/user) + ToastContext
│   └── router.jsx            # All routes with role-based guards
│
├── api/
│   ├── client.js             # Axios instance: Bearer token + 401 redirect
│   ├── auth.api.js           # /auth/* endpoints
│   ├── citizen.api.js        # /citizen/* endpoints
│   ├── officer.api.js        # /officer/* endpoints
│   └── admin.api.js          # /admin/* endpoints
│
├── utils/
│   ├── constants.js          # ROLES, STATUS_BADGE_MAP, SCHEME_LABELS, dropdowns
│   ├── formatters.js         # fmtDate, fmtCurrency, getRequiredDocuments()
│   ├── guards.js             # Token decode, isTokenExpired, getRoleHomePath()
│   ├── useApi.js             # useApi() and useMutation() custom hooks
│   └── i18n.js               # i18next config — English + Hindi translations
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.jsx     # Sidebar + topbar shell (role-aware navigation)
│   │   └── AppLayout.css
│   └── feedback/
│       ├── index.jsx         # StatusBadge, SchemeBadge, ConfidenceBar,
│       │                     # StatCard, EmptyState, ErrorAlert, Pagination
│       ├── ErrorBoundary.jsx # React class error boundary
│       └── LangSwitcher.jsx  # EN ↔ HI toggle button
│
└── features/
    ├── auth/
    │   ├── LoginPage.jsx     # Email/password login form
    │   ├── RegisterPage.jsx  # Citizen self-registration
    │   ├── ProfilePage.jsx   # Update name/phone/address/state
    │   └── Auth.css
    │
    ├── citizen/
    │   ├── ApplyPage.jsx          # 14-field application form with validation
    │   ├── ApplicationsPage.jsx   # List with confidence bars + status badges
    │   ├── ApplicationDetail.jsx  # Detail + AI prediction + document upload/verify
    │   └── NotificationsPage.jsx  # Notifications list + mark read
    │
    ├── officer/
    │   ├── QueuePage.jsx          # Priority queue (needs_review first) + stats
    │   ├── ApplicationsPage.jsx   # Filterable list by status/scheme
    │   └── ReviewPage.jsx         # Full review: SHAP, probabilities, decision panel
    │
    └── admin/
        ├── DashboardPage.jsx      # Stats + Recharts pie/bar + officer leaderboard
        ├── ApplicationsPage.jsx   # System-wide explorer with filters
        ├── ModelPage.jsx          # Accuracy/F1/fairness + confusion matrix image
        └── UsersPage.jsx          # User listing with roles
```

---

## Environment Variables

| Variable           | Default                          | Description              |
|--------------------|----------------------------------|--------------------------|
| `VITE_API_BASE_URL`| `http://localhost:8000/api/v1`  | FastAPI backend base URL |

---

## Roles & Routes

| Role    | Home Route              | Access                                      |
|---------|-------------------------|---------------------------------------------|
| citizen | `/citizen/applications` | Apply, track applications, notifications     |
| officer | `/officer/queue`        | Review queue, approve/reject with SHAP view  |
| admin   | `/admin/dashboard`      | Analytics, model metrics, user management    |

The router automatically redirects to the correct home after login, and blocks cross-role access.

---

## Key Features

### Citizen
- Multi-section application form with live validation mirroring backend constraints
- Conditional document checklist (Aadhaar always + BPL/Death/Disability cert based on answers)
- Drag-and-drop document upload per doc type with OCR verification status
- Notification feed with unread indicators and mark-all-read

### Officer
- Priority queue — `needs_review` applications floated to the top with warning styling
- Full review page with SHAP feature-importance bars and per-scheme probability breakdown
- Decision panel: approve/reject + optional scheme override + mandatory remarks
- Decision panel locks if decision already exists or application not in actionable state

### Admin
- Dashboard with Recharts PieChart (scheme distribution) + BarChart (status distribution)
- Officer activity leaderboard with medal icons
- Model metrics: accuracy/precision/recall/F1 + per-class table + confusion matrix image + SHAP summary image
- Fairness report table with flag indicators

---

## Manual Testing Checklist

- [ ] Login as citizen → redirected to `/citizen/applications`
- [ ] Login as officer → redirected to `/officer/queue`
- [ ] Login as admin  → redirected to `/admin/dashboard`
- [ ] Citizen submits application → sees AI prediction on detail page
- [ ] Citizen uploads Aadhaar, triggers verify → status updates
- [ ] Officer finds pending app → submits approve/reject with remarks
- [ ] Citizen sees updated status + new notification
- [ ] Admin dashboard numbers render without crash
- [ ] Upload wrong file type → frontend shows sensible error
- [ ] Navigate to wrong role's route → auto-redirect to own home
- [ ] Expire/remove token from localStorage → redirect to login

---

## Build for Production

```bash
npm run build
# Output in dist/
npm run preview   # Preview the production build locally
```

---

## Demo Credentials (seed these in your backend)

| Role    | Email                      | Password  |
|---------|----------------------------|-----------|
| citizen | test.citizen@nsap.com      | test1234  |
| officer | test.officer@nsap.com      | test1234  |
| admin   | test.admin@nsap.com        | test1234  |
