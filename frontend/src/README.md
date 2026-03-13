# Frontend Source

React + Tailwind CSS frontend — to be built.

## Structure (planned)
```
src/
├── components/
│   ├── ApplicantForm.jsx     ← main prediction form
│   ├── DocumentUpload.jsx    ← OCR document upload
│   ├── ResultCard.jsx        ← prediction result display
│   ├── OfficerDashboard.jsx  ← applications list + decisions
│   └── Navbar.jsx
├── pages/
│   ├── Home.jsx
│   ├── Apply.jsx
│   └── Dashboard.jsx
├── i18n/
│   ├── en.json               ← English translations
│   └── hi.json               ← Hindi translations
├── App.jsx
└── main.jsx
```

## Start frontend dev server
```bash
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173
