"""
Module: api/config.py
Description: Central configuration for NSAP Classification API.
             All constants, settings, environment variables and
             mock verification data live here.

             Keep feature lists in sync with NSAP_train.ipynb Section 3.
             Any change to features or thresholds in the notebook
             must be reflected here or inference will produce wrong results.

"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Project Root ─────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent
ML_MODELS_DIR = BASE_DIR / "ml_models"

# ─── Model Artifacts ──────────────────────────────────────────
CATBOOST_MODEL_PATH  = ML_MODELS_DIR / "nsap_catboost_model.cbm"
LABEL_ENCODER_PATH   = ML_MODELS_DIR / "nsap_label_encoder.pkl"
FEATURE_COLUMNS_PATH = ML_MODELS_DIR / "nsap_feature_columns.pkl"

# ─── NSAP Eligibility Rules ───────────────────────────────────
# BPL_THRESHOLD must match dataset_generator.py and notebook exactly.
# Changing this will break income_to_bpl_ratio feature engineering.
BPL_THRESHOLD = 72_000          # Annual income ceiling for BPL (INR)

# Minimum confidence to auto-approve a prediction.
# Below this → flagged for mandatory officer review.
# Matches notebook Section 3: CONF_THRESHOLD = 0.85
CONF_THRESHOLD = 0.85

# Priority order follows NSAP guidelines (WP > DP > OAP > NOT_ELIGIBLE)
PRIORITY_ORDER = ["WP", "DP", "OAP", "NOT_ELIGIBLE"]

# ─── Features ─────────────────────────────────────────────────
# Must match notebook Section 3 exactly — order matters for CatBoost.
CAT_FEATURES = [
    "gender", "marital_status", "bpl_card", "area_type",
    "social_category", "employment_status", "has_disability",
    "disability_type", "aadhaar_linked", "bank_account", "state",
]

# Includes 3 engineered interaction features computed before inference.
NUM_FEATURES = [
    "age",
    "annual_income",
    "disability_percentage",
    "age_x_disability_pct",   # age × disability_percentage / 100
    "income_to_bpl_ratio",    # annual_income / BPL_THRESHOLD
    "is_widowed_female",      # 1 if Female AND Widowed else 0
]

# Final feature order fed to CatBoost — do not reorder.
ALL_FEATURES = NUM_FEATURES + CAT_FEATURES

# ─── Feature Engineering ──────────────────────────────────────
def engineer_features(df):
    """
    Compute the 3 interaction features the model was trained with.
    Must be called on raw input before running inference.
    Mirrors logic in notebook Section 4.

    Args:
        df (pd.DataFrame): Raw applicant data.

    Returns:
        pd.DataFrame: DataFrame with 3 new interaction columns added.
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
# Local MySQL for development.
# In production replace with PlanetScale DATABASE_URL from .env
DB_HOST     = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "nsap_db")

# PlanetScale provides full URL — takes priority if set in .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ─── JWT Authentication ───────────────────────────────────────
SECRET_KEY         = os.getenv("SECRET_KEY", "change-this-in-production")
JWT_ALGORITHM      = "HS256"
JWT_EXPIRE_MINUTES = 1440       # 24 hours

# ─── Cloudinary (Document Storage) ───────────────────────────
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# ─── OCR ──────────────────────────────────────────────────────
TESSERACT_PATH     = os.getenv(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
MAX_UPLOAD_MB      = 10
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# ─── User Roles ───────────────────────────────────────────────
class UserRole:
    CITIZEN = "citizen"
    OFFICER = "officer"
    ADMIN   = "admin"

# ─── Application Status ───────────────────────────────────────
class AppStatus:
    PENDING       = "pending"        # just submitted, awaiting model
    AUTO_APPROVED = "auto_approved"  # confidence >= 85%, needs officer signoff
    NEEDS_REVIEW  = "needs_review"   # confidence < 85%, priority queue
    APPROVED      = "approved"       # officer signed off
    REJECTED      = "rejected"       # officer rejected

# ─── Document Types ───────────────────────────────────────────
class DocType:
    AADHAAR     = "aadhaar"
    BPL_CARD    = "bpl_card"
    DISABILITY  = "disability_certificate"
    DEATH_CERT  = "death_certificate"

# ─── Verification Status ──────────────────────────────────────
class VerificationStatus:
    PENDING  = "pending"
    VERIFIED = "verified"
    FAILED   = "failed"

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

# ─── Mock Verification Database ───────────────────────────────
# Simulates government portal verification.
# In production these would be real API calls to:
# UIDAI (Aadhaar), State portals (BPL), UDID (Disability), Civil registry (Death)
# Disclaimer: For prototype/demo purposes only.

VALID_AADHAAR = {
    "1234-5678-9012": {
        "name":     "Ram Kumar",
        "age":      65,
        "gender":   "Male",
        "state":    "Bihar",
        "area_type": "Rural"
    },
    "2345-6789-0123": {
        "name":     "Sita Devi",
        "age":      52,
        "gender":   "Female",
        "state":    "Uttar Pradesh",
        "area_type": "Rural"
    },
    "3456-7890-1234": {
        "name":     "Mohan Lal",
        "age":      72,
        "gender":   "Male",
        "state":    "Rajasthan",
        "area_type": "Rural"
    },
    "4567-8901-2345": {
        "name":     "Geeta Bai",
        "age":      45,
        "gender":   "Female",
        "state":    "Madhya Pradesh",
        "area_type": "Urban"
    },
    "5678-9012-3456": {
        "name":     "Arjun Singh",
        "age":      35,
        "gender":   "Male",
        "state":    "Bihar",
        "area_type": "Rural"
    },
    "6789-0123-4567": {
        "name":     "Kamla Devi",
        "age":      60,
        "gender":   "Female",
        "state":    "Uttar Pradesh",
        "area_type": "Rural"
    },
    "7890-1234-5678": {
        "name":     "Suresh Yadav",
        "age":      68,
        "gender":   "Male",
        "state":    "Madhya Pradesh",
        "area_type": "Rural"
    },
    "7138-3410-7816": {
        "name":     "Shubham Chaturvedi",
        "age":      68,
        "gender":   "Male",
        "state":    "Uttar Pradesh",
        "area_type": "Rural"
    },
}

VALID_BPL = {
    "BPL/UP/2023/001":  {"holder": "Ram Kumar",   "income": 32000},
    "BPL/BR/2023/002":  {"holder": "Sita Devi",   "income": 28000},
    "BPL/RJ/2023/003":  {"holder": "Mohan Lal",   "income": 35000},
    "BPL/MP/2023/004":  {"holder": "Geeta Bai",   "income": 30000},
    "BPL/BR/2023/005":  {"holder": "Arjun Singh",  "income": 25000},
    "BPL/UP/2023/006":  {"holder": "Kamla Devi",  "income": 27000},
    "BPL/MP/2023/007":  {"holder": "Suresh Yadav", "income": 31000},
}

VALID_DISABILITY = {
    "DIS/UP/2023/001": {"percentage": 65, "type": "Locomotor"},
    "DIS/BR/2023/002": {"percentage": 75, "type": "Visual"},
    "DIS/RJ/2023/003": {"percentage": 55, "type": "Hearing"},
    "DIS/MP/2023/004": {"percentage": 80, "type": "Intellectual"},
    "DIS/BR/2023/005": {"percentage": 45, "type": "Cerebral Palsy"},
    "DIS/UP/2023/006": {"percentage": 70, "type": "Multiple Disabilities"},
    "DIS/MP/2023/007": {"percentage": 60, "type": "Mental Illness"},
}

VALID_DEATH_CERT = {
    "DC/UP/2023/001": {"deceased": "Shyam Kumar",  "widow": "Sita Devi"},
    "DC/BR/2023/002": {"deceased": "Ramesh Lal",   "widow": "Geeta Bai"},
    "DC/RJ/2023/003": {"deceased": "Mohan Singh",  "widow": "Priya Devi"},
    "DC/MP/2023/004": {"deceased": "Rajesh Kumar", "widow": "Kamla Devi"},
    "DC/UP/2023/005": {"deceased": "Dinesh Yadav", "widow": "Meera Devi"},
}

# Invalid certificates for demo/testing rejection flow
INVALID_CERTIFICATES = {
    "FAKE/XX/0000/000",
    "1111-1111-1111",
    "BPL/XX/0000/000",
}