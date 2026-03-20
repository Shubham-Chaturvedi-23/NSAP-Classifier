"""
Module: api/routes/health.py
Description: Health check endpoint.
             Returns server status, model info and database
             connectivity for monitoring and deployment checks.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.models.database import get_db
from api.services.prediction import get_model_info

router = APIRouter(prefix="/health", tags=["Health"])


# ─── Health Check ─────────────────────────────────────────────
@router.get("")
def health_check(db: Session = Depends(get_db)):
    """
    GET /api/v1/health

    Returns server status, model info and database connectivity.
    Used by deployment platforms to verify service is running.

    Returns:
        dict: {
            status      (str):  "ok" if all systems healthy,
            timestamp   (str):  Current server time,
            model       (dict): Model type, classes, threshold,
            database    (str):  "connected" or "error"
        }
    """
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    # Get model info
    try:
        model_info = get_model_info()
        model_status = "loaded"
    except Exception:
        model_info   = {}
        model_status = "not loaded"

    return {
        "status":    "ok",
        "timestamp": datetime.now().isoformat(),
        "model": {
            "status": model_status,
            **model_info,
        },
        "database": db_status,
        "version":  "1.0.0",
    }