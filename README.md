# NSAP Scheme Classification System

Multi-role NSAP welfare scheme classifier with a FastAPI backend, React + Vite frontend, CatBoost inference, OCR, mock verification, and officer review workflow.

## Repository Contents

- `backend/` - FastAPI service, database models, OCR, verification, storage, notifications, and prediction logic.
- `frontend/` - React UI for citizens, officers, and admins.
- `ml/` - training notebooks and evaluation outputs.
- `sample_data/` - sample records for demos and testing.

## Current Layout

```text
NSAP Classifier/
├── backend/
│   ├── api/
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── ml_models/
│   ├── Testing/
│   ├── uploads/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── src/
│   └── .env.example
├── ml/
├── sample_data/
└── README.md
```

## Scheme Codes

| Code | Scheme |
|---|---|
| OAP | Indira Gandhi National Old Age Pension Scheme |
| WP | Indira Gandhi National Widow Pension Scheme |
| DP | Indira Gandhi National Disability Pension Scheme |
| NOT_ELIGIBLE | Not eligible for the target schemes |

## Roles

| Role | Purpose |
|---|---|
| Citizen | Register, submit applications, upload documents, track status, and read notifications |
| Officer | Review applications, inspect probabilities and SHAP values, and make final decisions |
| Admin | View analytics, model metrics, fairness reports, and user management screens |

## Flow

1. Citizen submits an application.
2. Citizen uploads documents.
3. OCR extracts document text and mock verification runs.
4. If verification succeeds, the CatBoost model predicts a scheme.
5. Low-confidence predictions are routed to `needs_review`.
6. Officer reviews the case and finalizes approve/reject decision.

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Shubham-Chaturvedi-23/NSAP-Classifier.git
cd "NSAP Classifier"
```

### 2. Create and activate the virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### 3. Install backend dependencies

```bash
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure backend environment variables

```bash
copy .env.example .env
```

Edit `backend/.env` with database, JWT, Cloudinary, and OCR settings.

### 5. Install frontend dependencies

```bash
cd ..\frontend
npm install
copy .env.example .env
```

### 6. Make sure model artifacts exist

The backend expects these files in `backend/api/ml_models/`:

- `nsap_catboost_model.cbm`
- `nsap_label_encoder.pkl`
- `nsap_feature_columns.pkl`

### 7. Start the backend

```bash
cd ..\backend
python run.py
```

API base URL: `http://localhost:8000`

### 8. Start the frontend

```bash
cd ..\frontend
npm run dev
```

Frontend dev URL: `http://localhost:5173`

## Useful Links

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Files

- `backend/.env.example`
- `frontend/.env.example`

## Development Notes

- The backend uses the exact Python interpreter from `.venv`.
- If the project was moved, recreate the venv to avoid stale absolute paths in activation scripts.
- Tesseract OCR is required for document processing.
- Cloudinary credentials are required for document uploads.

## Supporting Assets

- `ml/NSAP_train.ipynb` for training and experimentation.
- `ml/fairness_report.csv` and `ml/model_comparison.csv` for evaluation data.
- `sample_data/sample_5_records.csv` for quick local testing.
