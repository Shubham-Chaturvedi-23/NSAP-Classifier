# NSAP Scheme Classification System

**Multi-Class ML Model for NSAP Welfare Scheme Allocation**

G. L. Bajaj Group of Institutions, Mathura — Academic Year 2025-2026

---

## Team
| Name | Enrollment |
|---|---|
| Shubham Chaturvedi | 2205110100159 |
| Shreyash Singh | 2205110100156 |
| Harshit Maurya | 2205110100074 |
| Parth Sharma | 2205110100114 |

**Guide:** Er. Gaurav Kumar Singh, Assistant Professor (CSE Dept.)

---

## Project Overview

Automated multi-class classification system that assigns NSAP applicants to one of four categories:

| Scheme | Full Name | Beneficiary |
|---|---|---|
| OAP | Indira Gandhi National Old Age Pension Scheme | Elderly (60+) |
| WP | Indira Gandhi National Widow Pension Scheme | Widows (40-79) |
| DP | Indira Gandhi National Disability Pension Scheme | Specially Abled (18-79) |
| NOT_ELIGIBLE | — | Does not qualify |

---

## Project Structure

```
NSAP Classifier/
│
├── api/                        ← FastAPI backend
│   ├── app.py                  ← FastAPI entry point + lifespan
│   ├── routes.py               ← all API endpoints
│   ├── database.py             ← SQLAlchemy MySQL models
│   ├── ocr.py                  ← document upload + OCR extraction
│   └── __init__.py
│
├── frontend/                   ← React frontend (to be built)
│   ├── package.json
│   └── src/
│
├── models/                     ← trained model artifacts (not in git)
│   ├── nsap_catboost_model.cbm ← download from Colab
│   ├── nsap_label_encoder.pkl  ← download from Colab
│   └── nsap_feature_columns.pkl← download from Colab
│
├── sample_data/
│   └── sample_5_records.csv   ← 5 sample applicants for testing
│
├── uploads/                    ← temp OCR uploads (gitignored)
│
├── config.py                   ← all constants and settings
├── run.py                      ← start the API server
├── requirements.txt
├── .env                        ← credentials (gitignored)
├── .env.example                ← template for .env
└── .gitignore
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/nsap-classifier.git
cd nsap-classifier
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR
Download and install from:
https://github.com/UB-Mannheim/tesseract/wiki

Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 5. Set up environment file
```bash
copy .env.example .env
# Edit .env with your MySQL password
```

### 6. Place model files
Download from Google Colab outputs and place in `models/` folder:
- `nsap_catboost_model.cbm`
- `nsap_label_encoder.pkl`
- `nsap_feature_columns.pkl`

### 7. Create MySQL database
Open MySQL Workbench and run:
```sql
CREATE DATABASE nsap_db;
```
Tables are created automatically when the server starts.

### 8. Start the API
```bash
python run.py
```

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | Server health check |
| POST | `/api/v1/predict` | Single applicant prediction |
| POST | `/api/v1/predict/batch` | Batch prediction |
| POST | `/api/v1/ocr/extract` | Upload single document |
| POST | `/api/v1/ocr/extract/multiple` | Upload multiple documents |
| GET | `/api/v1/applications` | List all applications |
| GET | `/api/v1/applications/{id}` | Single application detail |
| POST | `/api/v1/applications/decision` | Officer approve/reject |
| GET | `/api/v1/stats` | Dashboard statistics |

---

## Model Performance (CatBoost — v3 Dataset)

| Metric | Score |
|---|---|
| Accuracy | ~88-92% |
| F1 Weighted | ~88-92% |
| False Not-Eligible Rate | < 5% |
| False Eligible Rate | < 5% |

Key features: `age`, `disability_percentage`, `annual_income`, `bpl_card`

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | CatBoost + SHAP |
| Backend | FastAPI + Uvicorn |
| Database | MySQL 8.0 + SQLAlchemy |
| OCR | Tesseract + OpenCV |
| Frontend | React 18 + Tailwind CSS |
| Training | Google Colab |

---

## Dataset

Synthetic dataset of 15,000 records generated to match NSAP national demographic distributions across 15 Indian states. Includes 13% label noise and 18% boundary cases for realistic model performance.

**Not included in this repo** — generate using `nsap_scheme_allocation_v3.py` in Google Colab.
