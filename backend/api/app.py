"""
api/app.py
==========
FastAPI application entry point.
Loads model artifacts on startup, registers all routes.
"""

import pickle
from contextlib import asynccontextmanager
from catboost import CatBoostClassifier
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import create_tables
from api.routes import router, load_model_artifacts
from config import (
    CATBOOST_MODEL_PATH, LABEL_ENCODER_PATH,
    FEATURE_COLUMNS_PATH, CORS_ORIGINS, API_PREFIX
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model artifacts and create DB tables on startup."""
    print("─" * 50)
    print("  NSAP Classification API — Starting up")
    print("─" * 50)

    # Create MySQL tables if they don't exist
    try:
        create_tables()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise

    # Load CatBoost model
    try:
        model = CatBoostClassifier()
        model.load_model(str(CATBOOST_MODEL_PATH))
        print(f"✅ CatBoost model loaded from {CATBOOST_MODEL_PATH.name}")
    except Exception as e:
        print(f"❌ Model load error: {e}")
        raise

    # Load label encoder
    try:
        with open(LABEL_ENCODER_PATH, "rb") as f:
            encoder = pickle.load(f)
        print(f"✅ Label encoder loaded — classes: {list(encoder.classes_)}")
    except Exception as e:
        print(f"❌ Encoder load error: {e}")
        raise

    # Load feature columns
    try:
        with open(FEATURE_COLUMNS_PATH, "rb") as f:
            features = pickle.load(f)
        print(f"✅ Feature columns loaded — {len(features)} features")
    except Exception as e:
        print(f"❌ Feature columns load error: {e}")
        raise

    # Inject into routes
    load_model_artifacts(model, encoder, features)

    print("─" * 50)
    print("  API ready at http://localhost:8000")
    print("  Docs    at http://localhost:8000/docs")
    print("─" * 50)

    yield

    print("NSAP API shutting down...")


# ─── App Instance ─────────────────────────────────────────────
app = FastAPI(
    title       = "NSAP Scheme Classification API",
    description = (
        "Multi-class ML model for NSAP welfare scheme allocation. "
        "Classifies applicants into OAP, WP, DP, or NOT_ELIGIBLE. "
        "Built by G. L. Bajaj Group of Institutions, Mathura."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = CORS_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ─── Routes ───────────────────────────────────────────────────
app.include_router(router, prefix=API_PREFIX)
