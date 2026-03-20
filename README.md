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

Automated multi-class classification system that assigns NSAP applicants
to one of four welfare scheme categories using CatBoost ML model with
role-based access for Citizens, Officers and Admins.

| Scheme | Full Name | Beneficiary |
|---|---|---|
| OAP | Indira Gandhi National Old Age Pension Scheme | Elderly (60+) |
| WP | Indira Gandhi National Widow Pension Scheme | Widows (40-79) |
| DP | Indira Gandhi National Disability Pension Scheme | Specially Abled (18-79) |
| NOT_ELIGIBLE | — | Does not qualify |

---

## Project Structure
```
NSAP CLASSIFIER/
│
├── backend/                         ← FastAPI backend
│   ├── api/
│   │   ├── app.py                   ← FastAPI entry point + lifespan
│   │   ├── config.py                ← all constants, settings, mock data
│   │   ├── __init__.py
│   │   │
│   │   ├── routes/
│   │   │   ├── auth.py              ← register, login, JWT
│   │   │   ├── citizen.py           ← apply, upload docs, track status
│   │   │   ├── officer.py           ← review queue, decisions
│   │   │   ├── admin.py             ← dashboard, model metrics
│   │   │   └── health.py            ← health check
│   │   │
│   │   ├── services/
│   │   │   ├── prediction.py        ← CatBoost inference + SHAP
│   │   │   ├── ocr.py               ← Tesseract OCR extraction
│   │   │   ├── verification.py      ← mock govt portal verification
│   │   │   ├── storage.py           ← Cloudinary document storage
│   │   │   └── notification.py      ← citizen status notifications
│   │   │
│   │   ├── models/
│   │   │   ├── database.py          ← SQLAlchemy session setup
│   │   │   ├── entities.py          ← DB table definitions (6 tables)
│   │   │   └── schemas.py           ← Pydantic request/response models
│   │   │
│   │   └── ml_models/               ← trained model artifacts (not in git)
│   │       ├── nsap_catboost_model.cbm
│   │       ├── nsap_label_encoder.pkl
│   │       └── nsap_feature_columns.pkl
│   │
│   ├── uploads/                     ← temp OCR uploads (gitignored)
│   ├── .env                         ← credentials (gitignored)
│   ├── .env.example                 ← template for .env
│   ├── requirements.txt
│   └── run.py                       ← start the API server
│
├── frontend/                        ← React frontend (to be built)
│
├── ml/                              ← ML training and analysis
│   ├── NSAP_train.ipynb             ← training pipeline (Google Colab)
│   ├── dataset_generator.py         ← synthetic dataset generator
│   ├── fairness_report.csv          ← per-demographic fairness metrics
│   ├── model_comparison.csv         ← model comparison metrics
│   └── output/                      ← generated plots and charts
│
├── sample_data/
│   └── sample_5_records.csv         ← 5 sample applicants for testing
│
└── README.md
```

---

## User Roles

| Role | Responsibilities |
|---|---|
| **Citizen** | Register, fill application form, upload documents, track status |
| **Officer** | Review applications, view SHAP explanations, approve/reject |
| **Admin** | Analytics dashboard, model metrics, fairness report, officer activity |

---

## Application Workflow
```
Citizen fills form + uploads documents
              ↓
OCR extracts fields → Mock verification
              ↓
Model predicts scheme + confidence
              ↓
       ┌──────┴──────┐
       ↓             ↓
  ≥ 85%           < 85%
confidence       confidence
       ↓             ↓
 auto_approved   needs_review
  (quick         (priority
  signoff)        queue)
       └──────┬──────┘
              ↓
      Officer Reviews
      (both cases need
      officer sign-off)
              ↓
      Final Decision
    (approve / reject)
              ↓
    Citizen notified
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Shubham-Chaturvedi-23/NSAP-Classifier.git
cd NSAP-Classifier
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
```

### 3. Install dependencies
```bash
cd backend
pip install catboost==1.2.10 --only-binary=catboost
pip install -r requirements.txt
```

### 4. Install Tesseract OCR
Download and install from:
https://github.com/UB-Mannheim/tesseract/wiki

Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 5. Set up environment file
```bash
copy .env.example .env
# Edit .env with your credentials
```

### 6. Place model files
Download from Google Colab outputs and place in `backend/api/ml_models/`:
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
cd backend
python run.py
```

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user profile |

### Citizen
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/citizen/apply` | Submit new application |
| POST | `/api/v1/citizen/documents/upload` | Upload and OCR documents |
| POST | `/api/v1/citizen/documents/verify` | Verify documents mock portal |
| GET | `/api/v1/citizen/applications` | List own applications |
| GET | `/api/v1/citizen/applications/{id}` | Single application detail |
| GET | `/api/v1/citizen/notifications` | Get notifications |

### Officer
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/officer/queue` | Priority review queue |
| GET | `/api/v1/officer/applications` | All applications |
| GET | `/api/v1/officer/applications/{id}` | Full detail with SHAP |
| POST | `/api/v1/officer/applications/{id}/decide` | Approve or reject |
| GET | `/api/v1/officer/stats` | Officer dashboard stats |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/admin/stats` | Full dashboard statistics |
| GET | `/api/v1/admin/model/metrics` | Model comparison metrics |
| GET | `/api/v1/admin/model/fairness` | Fairness report |
| GET | `/api/v1/admin/model/confusion` | Confusion matrix image |
| GET | `/api/v1/admin/model/shap` | SHAP feature importance |
| GET | `/api/v1/admin/officers/activity` | Officer performance |
| GET | `/api/v1/admin/users` | All registered users |

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | Server + model + DB status |

---

## Model Performance (CatBoost — v6 Dataset)

| Metric | Score |
|---|---|
| Accuracy | 93.16% |
| F1 Weighted | 93.15% |
| False Not-Eligible Rate | 1.7% |
| False Eligible Rate | 2.6% |
| Fairness Flags | 0 groups flagged |

Key features: `age`, `disability_percentage`, `annual_income`, `bpl_card`

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | CatBoost + SHAP + Optuna |
| Backend | FastAPI + Uvicorn |
| Database | MySQL 8.0 + SQLAlchemy |
| Authentication | JWT + bcrypt |
| OCR | Tesseract + OpenCV |
| Storage | Cloudinary |
| Frontend | React 18 + Tailwind CSS (to be built) |
| Training | Google Colab (T4 GPU) |
| Deployment | Railway + PlanetScale |

---

## Dataset

Synthetic dataset of 15,000 records generated to match NSAP national
demographic distributions across 15 Indian states.
Includes 7% label noise and 18% boundary cases for realistic performance.

Generate using:
```bash
cd ml
python dataset_generator.py
```

Output saved to `sample_data/` folder automatically.

---

## Document Verification

> **Disclaimer:** Government portal verification is simulated for prototype
> purposes. In production this would connect to authorized APIs:
> UIDAI (Aadhaar), State BPL portals, UDID (Disability), Civil Registry.

Supported documents:
| Document | Fields Extracted |
|---|---|
| Aadhaar Card | age, gender, state, area_type |
| BPL Card | annual_income, bpl_card status |
| Disability Certificate | disability_percentage, disability_type |
| Death Certificate | marital_status (Widowed) |