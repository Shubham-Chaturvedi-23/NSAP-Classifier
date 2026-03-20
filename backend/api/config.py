"""
config.py
=========
Central configuration for NSAP Classification API.
All constants and settings live here.

Keep this file in sync with NSAP_train.ipynb Section 3 (Configuration).
Any change to features, thresholds, or BPL_THRESHOLD in the notebook
must be reflected here or inference will silently produce wrong results.
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

# ─── NSAP Eligibility Rules ───────────────────────────────────
# BPL_THRESHOLD must match generate_nsap_dataset.py and the notebook exactly.
# Changing this value will break income_to_bpl_ratio feature engineering.
BPL_THRESHOLD  = 72_000          # Annual income ceiling for BPL eligibility (INR)

# Minimum model confidence to auto-approve a prediction.
# Predictions below this are flagged for manual officer review.
# Value from notebook Section 3: CONF_THRESHOLD = 0.85
# NOTE: config.py previously had 0.70 — corrected to match notebook.
CONF_THRESHOLD = 0.85

# When an applicant qualifies for multiple schemes, first match in this
# list wins. Order is defined by NSAP guidelines (WP > DP > OAP).
PRIORITY_ORDER = ["WP", "DP", "OAP", "NOT_ELIGIBLE"]

# ─── Features ─────────────────────────────────────────────────
# These lists must match the notebook (Section 3) exactly.
# The model was trained on ALL_FEATURES = NUM_FEATURES + CAT_FEATURES
# in that specific order — any deviation causes a feature mismatch at
# inference time.

CAT_FEATURES = [
    "gender", "marital_status", "bpl_card", "area_type",
    "social_category", "employment_status", "has_disability",
    "disability_type", "aadhaar_linked", "bank_account", "state",
]

# NUM_FEATURES includes 3 engineered interaction features that must be
# computed before passing data to the model (see feature_engineering()).
NUM_FEATURES = [
    "age",
    "annual_income",
    "disability_percentage",
    "age_x_disability_pct",   # age × disability_percentage / 100
    "income_to_bpl_ratio",    # annual_income / BPL_THRESHOLD
    "is_widowed_female",      # 1 if gender==Female AND marital_status==Widowed
]

# Final feature order fed to CatBoost — do not reorder.
ALL_FEATURES = NUM_FEATURES + CAT_FEATURES

# ─── Feature Engineering ──────────────────────────────────────
def engineer_features(df):
    """
    Compute the 3 interaction features the model was trained with.
    Call this on any raw input DataFrame before running inference.
    Mirrors the logic in notebook Section 4 and predict_applicant().
    """
    df = df.copy()
    df["age_x_disability_pct"] = df["age"] * df["disability_percentage"] / 100
    df["income_to_bpl_ratio"]  = df["annual_income"] / BPL_THRESHOLD
    df["is_widowed_female"]    = (
        (df["gender"] == "Female") & (df["marital_status"] == "Widowed")
    ).astype(int)
    return df

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