"""
config.py
=========
Central configuration for NSAP Classification API.
All constants and settings live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Project Root ─────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

# ─── Model Artifacts ──────────────────────────────────────────
CATBOOST_MODEL_PATH  = MODELS_DIR / "nsap_catboost_model.cbm"
LABEL_ENCODER_PATH   = MODELS_DIR / "nsap_label_encoder.pkl"
FEATURE_COLUMNS_PATH = MODELS_DIR / "nsap_feature_columns.pkl"

# ─── NSAP Rules ───────────────────────────────────────────────
CONF_THRESHOLD = 0.70
PRIORITY_ORDER = ["WP", "DP", "OAP", "NOT_ELIGIBLE"]

# ─── Features ─────────────────────────────────────────────────
CAT_FEATURES = [
    "gender", "marital_status", "bpl_card", "area_type",
    "social_category", "employment_status", "has_disability",
    "disability_type", "aadhaar_linked", "bank_account", "state"
]
NUM_FEATURES = ["age", "annual_income", "disability_percentage"]
ALL_FEATURES = NUM_FEATURES + CAT_FEATURES

# ─── API ──────────────────────────────────────────────────────
API_HOST    = "0.0.0.0"
API_PORT    = 8000
API_PREFIX  = "/api/v1"
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]

# ─── Database ─────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nsap1234")
DB_NAME     = os.getenv("DB_NAME", "nsap_db")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ─── OCR ──────────────────────────────────────────────────────
TESSERACT_PATH     = os.getenv(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
MAX_UPLOAD_MB      = 10
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# ─── Scheme Labels ────────────────────────────────────────────
SCHEME_LABELS = {
    "OAP":          "Old Age Pension (IGNOAPS)",
    "WP":           "Widow Pension (IGNWPS)",
    "DP":           "Disability Pension (IGNDPS)",
    "NOT_ELIGIBLE": "Not Eligible"
}

SCHEME_LABELS_HI = {
    "OAP":          "वृद्धावस्था पेंशन (IGNOAPS)",
    "WP":           "विधवा पेंशन (IGNWPS)",
    "DP":           "विकलांगता पेंशन (IGNDPS)",
    "NOT_ELIGIBLE": "पात्र नहीं"
}

# ─── Indian States ────────────────────────────────────────────
INDIAN_STATES = [
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu & Kashmir", "Puducherry", "Other"
]
