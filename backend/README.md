# Backend README

FastAPI backend for the NSAP Scheme Classification System.

## What This Service Does

- Accepts citizen applications.
- Stores application and user data in MySQL.
- Loads the CatBoost model and predicts OAP, WP, DP, or NOT_ELIGIBLE.
- Runs OCR on uploaded documents.
- Verifies documents against mock government data.
- Uploads files to Cloudinary.
- Exposes officer and admin workflows through a REST API.

## Main Entry Points

- [api/app.py](api/app.py)
- [run.py](run.py)
- [api/config.py](api/config.py)
- [api/services/prediction.py](api/services/prediction.py)

## Project Structure

```text
backend/
├── api/
│   ├── app.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── ml_models/
├── Testing/
├── uploads/
├── .env.example
├── requirements.txt
└── run.py
```

## Requirements

- Python 3.13
- MySQL
- Tesseract OCR
- Cloudinary account for uploads

## Installation

From the repository root:

```bash
python -m venv .venv
.\.venv\Scripts\activate.bat
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DATABASE_URL`
- `SECRET_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `TESSERACT_PATH`

## Model Artifacts

The backend expects these files in `api/ml_models/`:

- `nsap_catboost_model.cbm`
- `nsap_label_encoder.pkl`
- `nsap_feature_columns.pkl`

If any of them are missing, startup will fail when the model loader runs.

## Run the Backend

```bash
python run.py
```

The API starts on `http://localhost:8000`.

## API Base Path

All application routes are mounted under `/api/v1`.

Available routers:

- `/api/v1/auth`
- `/api/v1/citizen`
- `/api/v1/officer`
- `/api/v1/admin`
- `/api/v1/health`

## Startup Behavior

On startup, the service:

1. Creates database tables if they do not exist.
2. Loads the CatBoost model artifacts.
3. Checks Cloudinary connectivity.

## Notes on Documents

- Uploaded files are stored in Cloudinary.
- OCR handles image and PDF uploads.
- Missing Cloudinary credentials will disable document uploads.

## Related Files

- [api/routes/citizen.py](api/routes/citizen.py)
- [api/routes/officer.py](api/routes/officer.py)
- [api/routes/admin.py](api/routes/admin.py)
- [api/models/entities.py](api/models/entities.py)
- [api/models/schemas.py](api/models/schemas.py)
