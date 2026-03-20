"""
api/routes.py
=============
All API endpoints for NSAP Classification System.
"""

import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database import get_db, Application
from api.ocr import process_document
from config import (
    ALL_FEATURES, CAT_FEATURES, NUM_FEATURES,
    CONF_THRESHOLD, PRIORITY_ORDER,
    SCHEME_LABELS, SCHEME_LABELS_HI
)

router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────

class ApplicantInput(BaseModel):
    age:                   int   = Field(..., ge=18, le=120)
    gender:                str
    marital_status:        str
    annual_income:         int   = Field(..., ge=0)
    bpl_card:              str
    area_type:             str
    state:                 str
    social_category:       str
    employment_status:     str
    has_disability:        str
    disability_percentage: int   = Field(0, ge=0, le=100)
    disability_type:       str   = "None"
    aadhaar_linked:        str
    bank_account:          str

    class Config:
        json_schema_extra = {
            "example": {
                "age": 68, "gender": "Female", "marital_status": "Widowed",
                "annual_income": 35000, "bpl_card": "Yes", "area_type": "Rural",
                "state": "Uttar Pradesh", "social_category": "SC",
                "employment_status": "Unemployed", "has_disability": "No",
                "disability_percentage": 0, "disability_type": "None",
                "aadhaar_linked": "Yes", "bank_account": "Yes"
            }
        }


class PredictionResponse(BaseModel):
    application_id:   str
    predicted_scheme: str
    scheme_full_name: str
    scheme_full_name_hi: str
    confidence:       float
    needs_review:     bool
    all_qualifying:   List[str]
    all_probabilities: dict
    submitted_at:     str


class DecisionInput(BaseModel):
    application_id: str
    decision:       str   # APPROVED or REJECTED
    officer_note:   Optional[str] = None


class DecisionResponse(BaseModel):
    application_id: str
    status:         str
    decided_at:     str


# ─── Load model (called once on startup) ─────────────────────
_model   = None
_encoder = None
_features = None

def get_model():
    global _model, _encoder, _features
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check server startup logs."
        )
    return _model, _encoder, _features


def load_model_artifacts(model, encoder, features):
    """Called from app.py lifespan to inject loaded artifacts."""
    global _model, _encoder, _features
    _model    = model
    _encoder  = encoder
    _features = features


# ─── Prediction Helper ────────────────────────────────────────
def run_prediction(data: dict) -> dict:
    model, encoder, features = get_model()

    df_input = pd.DataFrame([data])[features]
    proba    = model.predict_proba(df_input)[0]
    classes  = list(encoder.classes_)

    # Priority-based scheme selection
    qualifying = [
        classes[i] for i, p in enumerate(proba)
        if p >= CONF_THRESHOLD and classes[i] != "NOT_ELIGIBLE"
    ]

    predicted  = "NOT_ELIGIBLE"
    confidence = float(np.max(proba))
    for scheme in PRIORITY_ORDER:
        if scheme in qualifying:
            predicted  = scheme
            confidence = float(proba[classes.index(scheme)])
            break

    return {
        "predicted_scheme":   predicted,
        "confidence":         round(confidence, 4),
        "needs_review":       confidence < CONF_THRESHOLD,
        "all_qualifying":     qualifying,
        "all_probabilities":  {
            cls: round(float(p), 4)
            for cls, p in zip(classes, proba)
        }
    }


# ─── Endpoints ────────────────────────────────────────────────

@router.get("/health")
def health_check():
    model, encoder, _ = get_model()
    return {
        "status":  "ok",
        "model":   "CatBoost",
        "classes": list(encoder.classes_),
        "time":    datetime.now().isoformat()
    }


@router.post("/predict", response_model=PredictionResponse)
def predict(data: ApplicantInput, db: Session = Depends(get_db)):
    """
    Submit applicant details and get NSAP scheme prediction.
    Saves result to database and returns prediction with confidence.
    """
    input_dict = data.model_dump()
    result     = run_prediction(input_dict)

    # Save to DB
    app = Application(
        **{k: v for k, v in input_dict.items()},
        predicted_scheme = result["predicted_scheme"],
        confidence       = result["confidence"],
        all_qualifying   = json.dumps(result["all_qualifying"]),
        needs_review     = result["needs_review"],
        status           = "PENDING",
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return PredictionResponse(
        application_id      = app.id,
        predicted_scheme    = result["predicted_scheme"],
        scheme_full_name    = SCHEME_LABELS.get(result["predicted_scheme"], ""),
        scheme_full_name_hi = SCHEME_LABELS_HI.get(result["predicted_scheme"], ""),
        confidence          = result["confidence"],
        needs_review        = result["needs_review"],
        all_qualifying      = result["all_qualifying"],
        all_probabilities   = result["all_probabilities"],
        submitted_at        = app.submitted_at.isoformat()
    )


@router.post("/predict/batch")
def predict_batch(data: List[ApplicantInput], db: Session = Depends(get_db)):
    """Submit multiple applicants at once."""
    results = []
    for item in data:
        input_dict = item.model_dump()
        result     = run_prediction(input_dict)

        app = Application(
            **{k: v for k, v in input_dict.items()},
            predicted_scheme = result["predicted_scheme"],
            confidence       = result["confidence"],
            all_qualifying   = json.dumps(result["all_qualifying"]),
            needs_review     = result["needs_review"],
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        results.append({
            "application_id":   app.id,
            "predicted_scheme": result["predicted_scheme"],
            "confidence":       result["confidence"],
            "needs_review":     result["needs_review"],
        })

    return {"total": len(results), "results": results}


@router.post("/ocr/extract")
async def ocr_extract(file: UploadFile = File(...)):
    """
    Upload a document (Aadhaar / Income Certificate /
    Disability Certificate / Death Certificate).
    Returns extracted fields ready to pre-fill the prediction form.
    """
    result = await process_document(file)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/ocr/extract/multiple")
async def ocr_extract_multiple(files: List[UploadFile] = File(...)):
    """
    Upload multiple documents at once.
    Merges extracted fields from all documents into one response.
    """
    merged   = {}
    doc_info = []

    for file in files:
        result = await process_document(file)
        doc_info.append({
            "filename":      result.get("filename"),
            "document_type": result.get("document_type"),
            "success":       result.get("success"),
        })
        if result["success"]:
            merged.update(result.get("extracted", {}))

    return {
        "success":   True,
        "documents": doc_info,
        "extracted": merged,
        "message":   f"Extracted fields from {len(files)} document(s). "
                     f"Please verify before submitting."
    }


@router.get("/applications")
def get_applications(
    status: Optional[str] = None,
    limit:  int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all applications with optional status filter."""
    query = db.query(Application)
    if status:
        query = query.filter(Application.status == status.upper())
    total = query.count()
    apps  = query.order_by(Application.submitted_at.desc()) \
                 .offset(offset).limit(limit).all()

    return {
        "total":  total,
        "limit":  limit,
        "offset": offset,
        "data": [
            {
                "id":               a.id,
                "submitted_at":     a.submitted_at.isoformat(),
                "predicted_scheme": a.predicted_scheme,
                "confidence":       a.confidence,
                "needs_review":     a.needs_review,
                "status":           a.status,
                "age":              a.age,
                "gender":           a.gender,
                "state":            a.state,
            }
            for a in apps
        ]
    }


@router.get("/applications/{application_id}")
def get_application(application_id: str, db: Session = Depends(get_db)):
    """Get full details of a single application."""
    app = db.query(Application).filter(
        Application.id == application_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "id":                    app.id,
        "submitted_at":          app.submitted_at.isoformat(),
        "age":                   app.age,
        "gender":                app.gender,
        "marital_status":        app.marital_status,
        "annual_income":         app.annual_income,
        "bpl_card":              app.bpl_card,
        "area_type":             app.area_type,
        "state":                 app.state,
        "social_category":       app.social_category,
        "employment_status":     app.employment_status,
        "has_disability":        app.has_disability,
        "disability_percentage": app.disability_percentage,
        "disability_type":       app.disability_type,
        "aadhaar_linked":        app.aadhaar_linked,
        "bank_account":          app.bank_account,
        "predicted_scheme":      app.predicted_scheme,
        "scheme_full_name":      SCHEME_LABELS.get(app.predicted_scheme, ""),
        "confidence":            app.confidence,
        "needs_review":          app.needs_review,
        "all_qualifying":        json.loads(app.all_qualifying or "[]"),
        "status":                app.status,
        "officer_note":          app.officer_note,
        "decided_at":            app.decided_at.isoformat() if app.decided_at else None,
    }


@router.post("/applications/decision", response_model=DecisionResponse)
def make_decision(data: DecisionInput, db: Session = Depends(get_db)):
    """Officer approves or rejects a pending application."""
    app = db.query(Application).filter(
        Application.id == data.application_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if data.decision.upper() not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED or REJECTED"
        )

    app.status       = data.decision.upper()
    app.officer_note = data.officer_note
    app.decided_at   = datetime.now()
    db.commit()
    db.refresh(app)

    return DecisionResponse(
        application_id = app.id,
        status         = app.status,
        decided_at     = app.decided_at.isoformat()
    )


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard statistics for officer portal."""
    total     = db.query(Application).count()
    pending   = db.query(Application).filter(Application.status == "PENDING").count()
    approved  = db.query(Application).filter(Application.status == "APPROVED").count()
    rejected  = db.query(Application).filter(Application.status == "REJECTED").count()
    review    = db.query(Application).filter(Application.needs_review == True).count()

    scheme_counts = {}
    for scheme in ["OAP", "WP", "DP", "NOT_ELIGIBLE"]:
        scheme_counts[scheme] = db.query(Application).filter(
            Application.predicted_scheme == scheme
        ).count()

    return {
        "total_applications": total,
        "pending":            pending,
        "approved":           approved,
        "rejected":           rejected,
        "needs_review":       review,
        "by_scheme":          scheme_counts,
    }
