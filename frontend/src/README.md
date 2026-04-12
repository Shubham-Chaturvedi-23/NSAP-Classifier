# Frontend README

React + Vite frontend for the NSAP Scheme Classification System.

## What This App Contains

- Public login and registration pages.
- Citizen application, detail, and notification pages.
- Officer queue and review pages.
- Admin dashboard, application explorer, model, and users pages.
- Shared layout, feedback, and utility components.

## Project Structure

```text
src/
├── main.jsx
├── styles/
├── app/
├── api/
├── components/
├── features/
└── utils/
```

## Main Frontend Files

- [src/main.jsx](src/main.jsx)
- [src/app/router.jsx](src/app/router.jsx)
- [src/app/providers.jsx](src/app/providers.jsx)
- [src/api/client.js](src/api/client.js)
- [src/utils/constants.js](src/utils/constants.js)
- [src/utils/guards.js](src/utils/guards.js)

## Prerequisites

- Node.js 18+
- npm 9+
- Backend running at `http://localhost:8000`

## Setup

From the `frontend/` folder:

```bash
npm install
copy .env.example .env
npm run dev
```

The dev server runs at `http://localhost:5173`.

## Environment Variables

The frontend currently uses:

- `VITE_API_BASE_URL` to point to the FastAPI backend, usually `http://localhost:8000/api/v1`

## Routes

| Route | Purpose |
|---|---|
| `/login` | Login page |
| `/register` | Citizen registration |
| `/profile` | Logged-in profile page |
| `/citizen/applications` | Citizen application list |
| `/citizen/apply` | Submit application |
| `/citizen/applications/:id` | Citizen application detail |
| `/citizen/notifications` | Citizen notifications |
| `/officer/queue` | Officer priority queue |
| `/officer/applications` | Officer application list |
| `/officer/applications/:id` | Officer review page |
| `/admin/dashboard` | Admin dashboard |
| `/admin/applications` | Admin application explorer |
| `/admin/model` | Model metrics page |
| `/admin/users` | User management page |

## Key Behaviors

- Auth state is stored in localStorage.
- The router redirects users to their role home path after login.
- Cross-role routes are blocked.
- The layout shell is role-aware.
- The app supports English and Hindi via the language switcher.

## Features By Role

### Citizen

- Submit the NSAP application form.
- View prediction results and application details.
- Upload and verify documents.
- Read application notifications.

### Officer

- Review `needs_review` applications first.
- Inspect probabilities and SHAP output.
- Approve or reject applications with remarks.

### Admin

- View dashboard analytics.
- Inspect model metrics and fairness output.
- Manage users and browse applications.

## Production Build

```bash
npm run build
npm run preview
```

The build output is written to `dist/`.

## Related Files

- [../index.html](../index.html)
- [../package.json](../package.json)
