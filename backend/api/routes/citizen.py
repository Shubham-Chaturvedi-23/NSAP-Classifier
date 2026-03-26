"""
Module: api/routes/citizen.py
Description: API endpoints for citizen role.
             Handles application submission, document upload,
             OCR processing, verification and status tracking.

Endpoints:
    POST /citizen/apply                  - Submit new application
    POST /citizen/documents/upload       - Upload and OCR documents
    POST /citizen/documents/verify       - Verify documents against mock portal
    GET  /citizen/applications           - List own applications
    GET  /citizen/applications/{id}      - Single application detail
    GET  /citizen/notifications          - Get notifications
    PUT  /citizen/notifications/read     - Mark all notifications read
    PUT  /citizen/notifications/{id}/read - Mark single notification read
"""

import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi import Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from api.models.database import get_db
from api.models.entities import Application, Document, Prediction
from api.models.schemas import (
    ApplicationCreate, ApplicationResponse,
    ApplicationSummary, NotificationResponse,
)
from api.routes.auth import require_citizen
from api.models.entities import User
from api.services.prediction import run_prediction
from api.services.ocr import process_document, process_multiple_documents
from api.services.verification import verify_document, get_verification_summary
from api.services.storage import upload_document
from api.services.notification import (
    notify_status_change, get_user_notifications,
    mark_as_read, mark_all_as_read, get_unread_count,
)
from api.config import AppStatus, SCHEME_LABELS, SCHEME_LABELS_HI

router = APIRouter(prefix="/citizen", tags=["Citizen"])


class VerifyDocumentsRequest(BaseModel):
    application_id: str


def _required_doc_types(application: Application) -> List[str]:
    required = ["aadhaar"]
    if application.bpl_card == "Yes":
        required.append("bpl_card")
    if application.marital_status == "Widowed":
        required.append("death_certificate")
    if application.has_disability == "Yes":
        required.append("disability_certificate")
    return required


# ─── Submit Application ───────────────────────────────────────
@router.post("/apply", status_code=status.HTTP_201_CREATED)
def submit_application(
    data:         ApplicationCreate,
    current_user: User    = Depends(require_citizen),
    db:           Session = Depends(get_db),
):
    """
    POST /api/v1/citizen/apply

    Submit a new NSAP scheme application.
    ML inference is deferred until document verification succeeds.

    Flow:
        1. Validate input fields
        2. Save Application with pending status
        3. Notify citizen that documents must be uploaded and verified
        4. Return application metadata (no prediction yet)

    Raises:
        HTTPException 400: If submission payload is invalid.
    """
    # Step 1 — Save Application in pending state
    application = Application(
        citizen_id            = current_user.id,
        status                = AppStatus.PENDING,
        age                   = data.age,
        gender                = data.gender,
        marital_status        = data.marital_status,
        annual_income         = data.annual_income,
        bpl_card              = data.bpl_card,
        area_type             = data.area_type,
        state                 = data.state,
        social_category       = data.social_category,
        employment_status     = data.employment_status,
        has_disability        = data.has_disability,
        disability_percentage = data.disability_percentage,
        disability_type       = data.disability_type,
        aadhaar_linked        = data.aadhaar_linked,
        bank_account          = data.bank_account,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Step 2 — Notify citizen of submission
    notify_status_change(
        db          = db,
        application = application,
        new_status  = AppStatus.PENDING,
    )

    # Step 3 — Build response
    return {
        "application_id":    application.id,
        "status":            application.status,
        "submitted_at":      application.submitted_at.isoformat(),
        "message": (
            "Application submitted successfully. "
            "Please upload and verify required documents to continue."
        ),
    }


# ─── Upload Documents ─────────────────────────────────────────
@router.post("/documents/upload")
async def upload_documents(
    application_id: str              = Form(...),
    declared_doc_type: Optional[str] = Form(None),
    files:          List[UploadFile] = File(...),
    current_user:   User             = Depends(require_citizen),
    db:             Session          = Depends(get_db),
):
    """
    POST /api/v1/citizen/documents/upload

    Upload one or more documents for an application.
    Runs OCR extraction and uploads to Cloudinary.

    Flow:
        1. Verify application belongs to current citizen
        2. Run OCR on each document
        3. Upload to Cloudinary
        4. Save Document records to database
        5. Return extracted fields for form verification

    Args:
        application_id (str):        Application UUID.
        files (List[UploadFile]):    Document files to upload.

    Raises:
        HTTPException 404: If application not found.
        HTTPException 403: If application belongs to another citizen.
    """
    # Step 1 — Verify application ownership
    application = db.query(Application).filter(
        Application.id         == application_id,
        Application.citizen_id == current_user.id,
    ).first()

    if not application:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Application not found.",
        )

    saved_docs   = []
    merged_fields = {}

    for file in files:
        # Step 2 — Read file bytes
        file_bytes = await file.read()

        # Step 3 — Run OCR
        from api.services.ocr import (
            load_image_from_bytes, extract_text,
            detect_document_type, extract_certificate_number,
        )
        import io
        from fastapi import UploadFile as FU

        # Re-create UploadFile with bytes for process_document
        from starlette.datastructures import UploadFile as StarletteUpload
        import io

        # Run OCR directly
        try:
            img      = load_image_from_bytes(file_bytes, file.filename)
            raw_text = extract_text(img)
            detected_doc_type = detect_document_type(raw_text)
            # For explicit UI uploads, trust the selected type first.
            # This avoids OCR misclassification hiding required docs.
            doc_type = declared_doc_type or detected_doc_type or "unknown"
            cert_num = extract_certificate_number(raw_text, doc_type)

            # Extract fields
            from api.services.ocr import (
                extract_aadhaar_fields, extract_bpl_fields,
                extract_disability_fields, extract_death_cert_fields,
            )
            extractors = {
                "aadhaar":               extract_aadhaar_fields,
                "bpl_card":              extract_bpl_fields,
                "disability_certificate": extract_disability_fields,
                "death_certificate":     extract_death_cert_fields,
            }
            extracted = {}
            if doc_type in extractors:
                extracted = extractors[doc_type](raw_text)

            merged_fields.update(extracted)

        except Exception:
            raw_text  = ""
            doc_type  = declared_doc_type or "unknown"
            cert_num  = None
            extracted = {}

        # Step 4 — Upload to Cloudinary
        try:
            upload_result = upload_document(
                file_bytes     = file_bytes,
                filename       = file.filename,
                application_id = application_id,
                doc_type       = doc_type,
            )
            file_url = upload_result["url"]
        except Exception:
            file_url = None

        # Step 5 — Save Document record
        doc = Document(
            application_id      = application_id,
            doc_type            = doc_type,
            file_url            = file_url,
            ocr_raw_text        = raw_text[:1000],
            extracted_data      = json.dumps(extracted),
            certificate_number  = cert_num,
            verification_status = "pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        saved_docs.append({
            "document_id":         doc.id,
            "doc_type":            doc_type,
            "file_url":            file_url,
            "certificate_number":  cert_num,
            "verification_status": "pending",
            "extracted":           extracted,
        })

    return {
        "success":        True,
        "documents":      saved_docs,
        "merged_fields":  merged_fields,
        "message": (
            f"Successfully processed {len(saved_docs)} document(s). "
            f"Please verify the extracted fields."
        ),
    }


# ─── Verify Documents ─────────────────────────────────────────
@router.post("/documents/verify")
def verify_documents(
    data:           VerifyDocumentsRequest,
    current_user:   User    = Depends(require_citizen),
    db:             Session = Depends(get_db),
):
    """
    POST /api/v1/citizen/documents/verify

    Run mock government portal verification on all uploaded documents
    for an application. Updates verification_status in database.

    Flow:
        1. Fetch all documents for application
        2. Run mock verification for each document
        3. Update verification_status in database
        4. Return verification summary

    Raises:
        HTTPException 404: If application not found.
    """
    application_id = data.application_id

    # Verify application ownership
    application = db.query(Application).filter(
        Application.id         == application_id,
        Application.citizen_id == current_user.id,
    ).first()

    if not application:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Application not found.",
        )

    required_doc_types = _required_doc_types(application)

    # Verify required documents only, using latest uploaded document per type.
    documents = []
    for required_type in required_doc_types:
        latest_doc = (
            db.query(Document)
            .filter(
                Document.application_id == application_id,
                Document.doc_type == required_type,
            )
            .order_by(Document.uploaded_at.desc())
            .first()
        )

        if not latest_doc:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail      = f"Missing required document: {required_type}",
            )

        documents.append(latest_doc)

    # Run verification for each document
    verification_results = []
    for doc in documents:
        result = verify_document(doc.doc_type, doc.certificate_number)

        # Update verification status in database
        doc.verification_status = result["status"]
        db.commit()

        verification_results.append({
            "document_id":         doc.id,
            "doc_type":            doc.doc_type,
            "certificate_number":  doc.certificate_number,
            "status":              result["status"],
            "message":             result["message"],
            "verified_data":       result["verified_data"],
        })

    # Build summary
    summary = get_verification_summary(verification_results)

    # If verification failed for any required document, reject immediately.
    if not summary["all_verified"]:
        application.status = AppStatus.REJECTED
        db.commit()

        notify_status_change(
            db          = db,
            application = application,
            new_status  = AppStatus.REJECTED,
            remarks     = "Document verification failed.",
        )

        return {
            "application_id":   application_id,
            "status":           application.status,
            "results":          verification_results,
            "all_verified":     False,
            "verified_count":   summary["verified_count"],
            "failed_count":     summary["failed_count"],
            "extracted_fields": summary["extracted_fields"],
            "message": (
                "One or more documents could not be verified. "
                "Application has been rejected."
            ),
        }

    # All documents verified: run ML now and push to officer queue.
    result = run_prediction({
        "age": application.age,
        "gender": application.gender,
        "marital_status": application.marital_status,
        "annual_income": application.annual_income,
        "bpl_card": application.bpl_card,
        "area_type": application.area_type,
        "state": application.state,
        "social_category": application.social_category,
        "employment_status": application.employment_status,
        "has_disability": application.has_disability,
        "disability_percentage": application.disability_percentage,
        "disability_type": application.disability_type,
        "aadhaar_linked": application.aadhaar_linked,
        "bank_account": application.bank_account,
    })

    if application.prediction:
        application.prediction.predicted_scheme = result["predicted_scheme"]
        application.prediction.confidence_score = result["confidence_score"]
        application.prediction.all_probabilities = json.dumps(result["all_probabilities"])
        application.prediction.needs_review = result["needs_review"]
        application.prediction.shap_values = (
            json.dumps(result["shap_values"])
            if result["shap_values"] else None
        )
    else:
        prediction = Prediction(
            application_id    = application.id,
            predicted_scheme  = result["predicted_scheme"],
            confidence_score  = result["confidence_score"],
            all_probabilities = json.dumps(result["all_probabilities"]),
            needs_review      = result["needs_review"],
            shap_values       = json.dumps(result["shap_values"])
                                if result["shap_values"] else None,
        )
        db.add(prediction)

    application.status = (
        AppStatus.AUTO_APPROVED
        if not result["needs_review"]
        else AppStatus.NEEDS_REVIEW
    )
    db.commit()

    notify_status_change(
        db          = db,
        application = application,
        new_status  = application.status,
    )

    return {
        "application_id":   application_id,
        "status":           application.status,
        "predicted_scheme": result["predicted_scheme"],
        "scheme_full_name": result["scheme_full_name"],
        "confidence_score": result["confidence_score"],
        "needs_review":     result["needs_review"],
        "results":          verification_results,
        "all_verified":     True,
        "verified_count":   summary["verified_count"],
        "failed_count":     summary["failed_count"],
        "extracted_fields": summary["extracted_fields"],
        "message":          "Documents verified. Application sent for officer review.",
    }


# ─── List Applications ────────────────────────────────────────
@router.get("/applications")
def get_my_applications(
    status_filter: Optional[str] = None,
    limit:         int           = 10,
    offset:        int           = 0,
    current_user:  User          = Depends(require_citizen),
    db:            Session       = Depends(get_db),
):
    """
    GET /api/v1/citizen/applications

    List all applications submitted by current citizen.
    Supports optional status filter and pagination.

    Args:
        status_filter (str): Filter by status (optional).
        limit         (int): Max results to return (default 10).
        offset        (int): Pagination offset (default 0).

    Returns:
        dict: Paginated list of application summaries.
    """
    query = db.query(Application).filter(
        Application.citizen_id == current_user.id
    )

    if status_filter:
        query = query.filter(Application.status == status_filter)

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
        results.append({
            "id":               app.id,
            "status":           app.status,
            "submitted_at":     app.submitted_at.isoformat(),
            "state":            app.state,
            "age":              app.age,
            "gender":           app.gender,
            "predicted_scheme": app.prediction.predicted_scheme
                                if app.prediction else None,
            "confidence_score": app.prediction.confidence_score
                                if app.prediction else None,
            "needs_review":     app.prediction.needs_review
                                if app.prediction else None,
            "scheme_full_name": SCHEME_LABELS.get(
                app.prediction.predicted_scheme, ""
            ) if app.prediction else "",
        })

    return {
        "total":  total,
        "limit":  limit,
        "offset": offset,
        "data":   results,
    }


# ─── Single Application Detail ────────────────────────────────
@router.get("/applications/{application_id}")
def get_application_detail(
    application_id: str,
    current_user:   User    = Depends(require_citizen),
    db:             Session = Depends(get_db),
):
    """
    GET /api/v1/citizen/applications/{application_id}

    Get full details of a single application including
    prediction, documents and decision.

    Raises:
        HTTPException 404: If application not found.
        HTTPException 403: If application belongs to another citizen.
    """
    app = db.query(Application).filter(
        Application.id         == application_id,
        Application.citizen_id == current_user.id,
    ).first()

    if not app:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Application not found.",
        )

    # Build prediction detail
    prediction_data = None
    if app.prediction:
        prediction_data = {
            "predicted_scheme":  app.prediction.predicted_scheme,
            "scheme_full_name":  SCHEME_LABELS.get(
                app.prediction.predicted_scheme, ""
            ),
            "scheme_full_name_hi": SCHEME_LABELS_HI.get(
                app.prediction.predicted_scheme, ""
            ),
            "confidence_score":  app.prediction.confidence_score,
            "needs_review":      app.prediction.needs_review,
            "all_probabilities": json.loads(
                app.prediction.all_probabilities or "{}"
            ),
            "shap_values": json.loads(
                app.prediction.shap_values or "{}"
            ),
        }

    # Build documents detail
    documents_data = [
        {
            "id":                  doc.id,
            "doc_type":            doc.doc_type,
            "file_url":            doc.file_url,
            "certificate_number":  doc.certificate_number,
            "verification_status": doc.verification_status,
            "uploaded_at":         doc.uploaded_at.isoformat(),
        }
        for doc in app.documents
    ]

    # Build decision detail
    decision_data = None
    if app.decision:
        decision_data = {
            "decision":       app.decision.decision,
            "remarks":        app.decision.remarks,
            "override_scheme": app.decision.override_scheme,
            "decided_at":     app.decision.decided_at.isoformat(),
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
        "prediction":            prediction_data,
        "documents":             documents_data,
        "decision":              decision_data,
    }


@router.put("/applications/{application_id}")
def update_application(
    application_id: str,
    data:           ApplicationCreate,
    current_user:   User    = Depends(require_citizen),
    db:             Session = Depends(get_db),
):
    """
    PUT /api/v1/citizen/applications/{application_id}

    Update a citizen application before document upload/verification.
    Edit is allowed only while status is pending and no documents exist.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.citizen_id == current_user.id,
    ).first()

    if not app:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Application not found.",
        )

    if app.status != AppStatus.PENDING:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Only pending applications can be edited.",
        )

    has_documents = db.query(Document).filter(
        Document.application_id == app.id
    ).first() is not None

    if has_documents or app.prediction:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Application cannot be edited after document upload.",
        )

    app.age                   = data.age
    app.gender                = data.gender
    app.marital_status        = data.marital_status
    app.annual_income         = data.annual_income
    app.bpl_card              = data.bpl_card
    app.area_type             = data.area_type
    app.state                 = data.state
    app.social_category       = data.social_category
    app.employment_status     = data.employment_status
    app.has_disability        = data.has_disability
    app.disability_percentage = data.disability_percentage
    app.disability_type       = data.disability_type
    app.aadhaar_linked        = data.aadhaar_linked
    app.bank_account          = data.bank_account

    db.commit()
    db.refresh(app)

    return {
        "application_id": app.id,
        "status":         app.status,
        "updated_at":     app.updated_at.isoformat(),
        "message":        "Application updated successfully.",
    }


# ─── Notifications ────────────────────────────────────────────
@router.get("/notifications")
def get_notifications(
    unread_only:  bool    = False,
    limit:        int     = 20,
    current_user: User    = Depends(require_citizen),
    db:           Session = Depends(get_db),
):
    """
    GET /api/v1/citizen/notifications

    Get notifications for current citizen.
    Supports filtering to unread only.

    Args:
        unread_only (bool): If True return only unread (default False).
        limit       (int):  Max notifications to return (default 20).

    Returns:
        dict: Notifications list with unread count.
    """
    notifications = get_user_notifications(
        db          = db,
        user_id     = current_user.id,
        unread_only = unread_only,
        limit       = limit,
    )
    unread_count = get_unread_count(db, current_user.id)

    return {
        "unread_count":  unread_count,
        "notifications": [
            {
                "id":             n.id,
                "message":        n.message,
                "is_read":        n.is_read,
                "created_at":     n.created_at.isoformat(),
                "application_id": n.application_id,
            }
            for n in notifications
        ],
    }


@router.put("/notifications/read")
def mark_notifications_read(
    current_user: User    = Depends(require_citizen),
    db:           Session = Depends(get_db),
):
    """
    PUT /api/v1/citizen/notifications/read

    Mark all notifications as read for current citizen.

    Returns:
        dict: Count of notifications marked as read.
    """
    count = mark_all_as_read(db, current_user.id)
    return {
        "marked_read": count,
        "message":     f"{count} notification(s) marked as read.",
    }


@router.put("/notifications/{notification_id}/read")
def mark_single_notification_read(
    notification_id: str,
    current_user:    User    = Depends(require_citizen),
    db:              Session = Depends(get_db),
):
    """
    PUT /api/v1/citizen/notifications/{notification_id}/read

    Mark a single notification as read.

    Raises:
        HTTPException 404: If notification not found.
    """
    success = mark_as_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = "Notification not found.",
        )
    return {"message": "Notification marked as read."}