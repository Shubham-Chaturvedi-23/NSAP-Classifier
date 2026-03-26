"""
Module: api/routes/officer.py
Description: API endpoints for officer role.
             Handles application review queue, detailed application
             view with SHAP explanations, and approve/reject decisions.

Endpoints:
    GET  /officer/queue                    - Priority review queue
    GET  /officer/applications             - All applications
    GET  /officer/applications/{id}        - Full application detail
    POST /officer/applications/{id}/decide - Approve or reject
    GET  /officer/stats                    - Officer dashboard stats
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.models.database import get_db
from api.models.entities import Application, Decision, Prediction, User
from api.models.schemas import DecisionCreate, DecisionResponse
from api.routes.auth import require_officer
from api.services.notification import notify_status_change
from api.services.prediction import run_prediction
from api.config import AppStatus, SCHEME_LABELS, SCHEME_LABELS_HI

router = APIRouter(prefix="/officer", tags=["Officer"])


# ─── Review Queue ─────────────────────────────────────────────
@router.get("/queue")
def get_review_queue(
    limit:        int     = 20,
    offset:       int     = 0,
    current_user: User    = Depends(require_officer),
    db:           Session = Depends(get_db),
):
    """
    GET /api/v1/officer/queue

    Get priority review queue — applications needing officer attention.
    Ordered by priority:
        1. needs_review first (low confidence — most urgent)
        2. auto_approved second (high confidence — quick signoff)
    Within each group ordered by submission date (oldest first).

    Args:
        limit  (int): Max results (default 20).
        offset (int): Pagination offset (default 0).

    Returns:
        dict: Paginated queue with counts by priority.
    """
    # Fetch needs_review applications first (low confidence — urgent)
    needs_review = db.query(Application).filter(
        Application.status == AppStatus.NEEDS_REVIEW
    ).order_by(Application.submitted_at.asc()).all()

    # Then auto_approved (high confidence — quick signoff)
    auto_approved = db.query(Application).filter(
        Application.status == AppStatus.AUTO_APPROVED
    ).order_by(Application.submitted_at.asc()).all()

    # Combine — needs_review always comes first
    all_pending = needs_review + auto_approved
    total       = len(all_pending)
    paginated   = all_pending[offset: offset + limit]

    results = []
    for app in paginated:
        results.append({
            "id":               app.id,
            "status":           app.status,
            "priority":         "high" if app.status == AppStatus.NEEDS_REVIEW
                                else "normal",
            "submitted_at":     app.submitted_at.isoformat(),
            "age":              app.age,
            "gender":           app.gender,
            "state":            app.state,
            "predicted_scheme": app.prediction.predicted_scheme
                                if app.prediction else None,
            "confidence_score": app.prediction.confidence_score
                                if app.prediction else None,
            "needs_review":     app.prediction.needs_review
                                if app.prediction else None,
            "scheme_full_name": SCHEME_LABELS.get(
                app.prediction.predicted_scheme, ""
            ) if app.prediction else "",
            "docs_verified":    all(
                d.verification_status == "verified"
                for d in app.documents
            ) if app.documents else False,
        })

    return {
        "total":              total,
        "needs_review_count": len(needs_review),
        "auto_approved_count": len(auto_approved),
        "limit":              limit,
        "offset":             offset,
        "queue":              results,
    }


# ─── All Applications ─────────────────────────────────────────
@router.get("/applications")
def get_all_applications(
    status_filter: Optional[str] = None,
    scheme_filter: Optional[str] = None,
    state_filter:  Optional[str] = None,
    limit:         int           = 20,
    offset:        int           = 0,
    current_user:  User          = Depends(require_officer),
    db:            Session       = Depends(get_db),
):
    """
    GET /api/v1/officer/applications

    List all applications with optional filters.
    Officers can see all applications regardless of citizen.

    Args:
        status_filter (str): Filter by application status.
        scheme_filter (str): Filter by predicted scheme.
        state_filter  (str): Filter by applicant state.
        limit         (int): Max results (default 20).
        offset        (int): Pagination offset (default 0).

    Returns:
        dict: Paginated application list.
    """
    # Officers should only see applications that have completed
    # document verification and ML prediction.
    query = db.query(Application).join(Prediction)

    if status_filter:
        query = query.filter(Application.status == status_filter)
    if state_filter:
        query = query.filter(Application.state == state_filter)

    total = query.count()
    apps  = (
        query
        .order_by(Application.submitted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for app in apps:
        # Apply scheme filter after join (prediction is a relationship)
        if scheme_filter and app.prediction:
            if app.prediction.predicted_scheme != scheme_filter:
                continue

        results.append({
            "id":               app.id,
            "status":           app.status,
            "submitted_at":     app.submitted_at.isoformat(),
            "age":              app.age,
            "gender":           app.gender,
            "state":            app.state,
            "social_category":  app.social_category,
            "predicted_scheme": app.prediction.predicted_scheme
                                if app.prediction else None,
            "confidence_score": app.prediction.confidence_score
                                if app.prediction else None,
            "needs_review":     app.prediction.needs_review
                                if app.prediction else None,
            "scheme_full_name": SCHEME_LABELS.get(
                app.prediction.predicted_scheme, ""
            ) if app.prediction else "",
            "has_decision":     app.decision is not None,
        })

    return {
        "total":  total,
        "limit":  limit,
        "offset": offset,
        "data":   results,
    }


# ─── Full Application Detail ──────────────────────────────────
@router.get("/applications/{application_id}")
def get_application_detail(
    application_id: str,
    current_user:   User    = Depends(require_officer),
    db:             Session = Depends(get_db),
):
    """
    GET /api/v1/officer/applications/{application_id}

    Get full application detail for officer review.
    Includes:
        - All applicant fields
        - Model prediction with confidence
        - SHAP feature importance for explainability
        - All uploaded documents with verification status
        - Citizen details
        - Previous decision (if any)

    Raises:
        HTTPException 404: If application not found.
    """
    app = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not app:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Application not found.",
        )

    if not app.prediction:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Application is not ready for officer review.",
        )

    # Backfill SHAP values for older predictions that were saved without it.
    if not app.prediction.shap_values:
        try:
            backfill = run_prediction({
                "age": app.age,
                "gender": app.gender,
                "marital_status": app.marital_status,
                "annual_income": app.annual_income,
                "bpl_card": app.bpl_card,
                "area_type": app.area_type,
                "state": app.state,
                "social_category": app.social_category,
                "employment_status": app.employment_status,
                "has_disability": app.has_disability,
                "disability_percentage": app.disability_percentage,
                "disability_type": app.disability_type,
                "aadhaar_linked": app.aadhaar_linked,
                "bank_account": app.bank_account,
            })
            if backfill.get("shap_values"):
                app.prediction.shap_values = json.dumps(backfill["shap_values"])
                db.commit()
                db.refresh(app.prediction)
        except Exception:
            pass

    # Build prediction with SHAP explanation
    prediction_data = None
    if app.prediction:
        shap_raw = json.loads(app.prediction.shap_values or "{}")
        prediction_data = {
            "predicted_scheme":    app.prediction.predicted_scheme,
            "scheme_full_name":    SCHEME_LABELS.get(
                app.prediction.predicted_scheme, ""
            ),
            "scheme_full_name_hi": SCHEME_LABELS_HI.get(
                app.prediction.predicted_scheme, ""
            ),
            "confidence_score":    app.prediction.confidence_score,
            "needs_review":        app.prediction.needs_review,
            "all_probabilities":   json.loads(
                app.prediction.all_probabilities or "{}"
            ),
            # SHAP values help officer understand why model predicted this
            "shap_explanation":    shap_raw,
            "created_at":          app.prediction.created_at.isoformat(),
        }

    # Build citizen info
    citizen_data = None
    if app.citizen:
        citizen_data = {
            "id":    app.citizen.id,
            "name":  app.citizen.name,
            "email": app.citizen.email,
            "phone": app.citizen.phone,
            "state": app.citizen.state,
        }

    # Build documents with verification
    documents_data = [
        {
            "id":                  doc.id,
            "doc_type":            doc.doc_type,
            "file_url":            doc.file_url,
            "certificate_number":  doc.certificate_number,
            "verification_status": doc.verification_status,
            "extracted_data":      json.loads(
                doc.extracted_data or "{}"
            ),
            "uploaded_at":         doc.uploaded_at.isoformat(),
        }
        for doc in app.documents
    ]

    # Build previous decision if exists
    decision_data = None
    if app.decision:
        decision_data = {
            "decision":        app.decision.decision,
            "remarks":         app.decision.remarks,
            "override_scheme": app.decision.override_scheme,
            "decided_at":      app.decision.decided_at.isoformat(),
            "officer_id":      app.decision.officer_id,
        }

    return {
        "id":                    app.id,
        "status":                app.status,
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
        "citizen":               citizen_data,
        "prediction":            prediction_data,
        "documents":             documents_data,
        "decision":              decision_data,
    }


# ─── Make Decision ────────────────────────────────────────────
@router.post("/applications/{application_id}/decide",
             response_model=DecisionResponse,
             status_code=status.HTTP_201_CREATED)
def make_decision(
    application_id: str,
    data:           DecisionCreate,
    current_user:   User    = Depends(require_officer),
    db:             Session = Depends(get_db),
):
    """
    POST /api/v1/officer/applications/{application_id}/decide

    Officer approves or rejects an application.
    Can optionally override the model's predicted scheme.

    Flow:
        1. Verify application exists and is pending decision
        2. Create Decision record
        3. Update Application status
        4. Notify citizen of final decision
        5. Return decision details

    Args:
        application_id (str):          Application UUID.
        data (DecisionCreate):         Decision details.

    Raises:
        HTTPException 404: If application not found.
        HTTPException 400: If application already decided.
    """
    # Step 1 — Fetch application
    app = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not app:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Application not found.",
        )

    # Prevent duplicate decisions
    if app.decision:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Decision already made for this application.",
        )

    # Only pending applications can be decided
    if app.status not in [AppStatus.AUTO_APPROVED, AppStatus.NEEDS_REVIEW]:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = f"Cannot decide application with status: {app.status}",
        )

    # Resolve final decision from final scheme selection.
    # NOT_ELIGIBLE always means rejection; any payable scheme means approval.
    resolved_decision = data.decision
    if data.override_scheme == "NOT_ELIGIBLE":
        resolved_decision = "rejected"
    elif data.override_scheme in {"OAP", "WP", "DP"}:
        resolved_decision = "approved"

    # Step 2 — Create Decision record
    decision = Decision(
        application_id  = application_id,
        officer_id      = current_user.id,
        decision        = resolved_decision,
        remarks         = data.remarks,
        override_scheme = data.override_scheme,
    )
    db.add(decision)

    # Step 3 — Update Application status
    app.status     = resolved_decision
    app.officer_id = current_user.id
    db.commit()
    db.refresh(decision)

    # Step 4 — Notify citizen
    notify_status_change(
        db          = db,
        application = app,
        new_status  = resolved_decision,
        remarks     = data.remarks,
    )

    return decision


# ─── Officer Stats ────────────────────────────────────────────
@router.get("/stats")
def get_officer_stats(
    current_user: User    = Depends(require_officer),
    db:           Session = Depends(get_db),
):
    """
    GET /api/v1/officer/stats

    Personal dashboard statistics for the logged-in officer.
    Shows their own decision history and pending queue counts.

    Returns:
        dict: Officer personal statistics.
    """
    # Queue counts
    needs_review_count  = db.query(Application).filter(
        Application.status == AppStatus.NEEDS_REVIEW
    ).count()

    auto_approved_count = db.query(Application).filter(
        Application.status == AppStatus.AUTO_APPROVED
    ).count()

    # This officer's decisions
    my_decisions = db.query(Decision).filter(
        Decision.officer_id == current_user.id
    ).all()

    total_decided  = len(my_decisions)
    total_approved = sum(1 for d in my_decisions if d.decision == "approved")
    total_rejected = sum(1 for d in my_decisions if d.decision == "rejected")
    total_overrides = sum(1 for d in my_decisions if d.override_scheme)

    # Today's decisions
    today = datetime.now().date()
    decisions_today = sum(
        1 for d in my_decisions
        if d.decided_at and d.decided_at.date() == today
    )

    return {
        "officer_name":       current_user.name,
        "queue": {
            "needs_review":   needs_review_count,
            "auto_approved":  auto_approved_count,
            "total_pending":  needs_review_count + auto_approved_count,
        },
        "my_decisions": {
            "total":          total_decided,
            "approved":       total_approved,
            "rejected":       total_rejected,
            "overrides":      total_overrides,
            "today":          decisions_today,
        },
    }