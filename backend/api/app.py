"""
Module: api/app.py
Description: FastAPI application entry point.
             Configures middleware, registers all routers
             and manages application lifespan — model loading
             and database table creation on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models.database import create_tables
from api.services.prediction import load_model_artifacts
from api.services.storage import check_cloudinary_connection
from api.routes.health import router as health_router
from api.routes.auth import router as auth_router
from api.routes.citizen import router as citizen_router
from api.routes.officer import router as officer_router
from api.routes.admin import router as admin_router
from api.config import CORS_ORIGINS, API_PREFIX


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.

    Startup:
        1. Create database tables if not exist
        2. Load CatBoost model artifacts
        3. Verify Cloudinary connection

    Shutdown:
        - Log shutdown message
    """
    # ── Startup ───────────────────────────────────────────────
    print("\n" + "─" * 52)
    print("   NSAP Classification API — Starting up")
    print("─" * 52)

    # Step 1 — Create database tables
    try:
        create_tables()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise

    # Step 2 — Load ML model artifacts
    try:
        load_model_artifacts()
    except Exception as e:
        print(f"❌ Model load error: {e}")
        raise

    # Step 3 — Verify Cloudinary (non-blocking — warn only)
    try:
        if check_cloudinary_connection():
            print("✅ Cloudinary connected")
        else:
            print("⚠️  Cloudinary not configured — document upload disabled")
    except Exception:
        print("⚠️  Cloudinary check failed — document upload may not work")

    print("─" * 52)
    print("   API ready at    http://localhost:8000")
    print("   Swagger UI at   http://localhost:8000/docs")
    print("   ReDoc at        http://localhost:8000/redoc")
    print("─" * 52 + "\n")

    yield

    # ── Shutdown ──────────────────────────────────────────────
    print("\nNSAP Classification API — Shutting down...")


# ─── App Instance ─────────────────────────────────────────────
app = FastAPI(
    title       = "NSAP Scheme Classification API",
    description = (
        "Multi-class ML model for NSAP welfare scheme allocation. \n\n"
        "Classifies applicants into OAP, WP, DP or NOT_ELIGIBLE "
        "using CatBoost with SHAP explainability.\n\n"
        "**Roles:** Citizen | Officer | Admin\n\n"
        "**Auth:** JWT Bearer token — use `/api/v1/auth/login` to get token."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)


# ─── CORS Middleware ──────────────────────────────────────────
# Allow React frontend (localhost:3000 / localhost:5173) to
# make cross-origin requests to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = CORS_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─── Routers ──────────────────────────────────────────────────
# All routes are prefixed with /api/v1
app.include_router(health_router,  prefix=API_PREFIX)
app.include_router(auth_router,    prefix=API_PREFIX)
app.include_router(citizen_router, prefix=API_PREFIX)
app.include_router(officer_router, prefix=API_PREFIX)
app.include_router(admin_router,   prefix=API_PREFIX)


# ─── Root Redirect ────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")