"""
Module: api/models/schemas.py
Description: Pydantic models for request validation and response serialization.
             Organized by role — Auth, Citizen, Officer, Admin.
             All request bodies and response shapes are defined here.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field


# ─── Auth Schemas ─────────────────────────────────────────────

class UserRegister(BaseModel):
    """Request body for citizen/officer registration."""
    name:     str       = Field(..., min_length=2,  max_length=100)
    email:    EmailStr
    phone:    Optional[str] = Field(None, max_length=15)
    password: str       = Field(..., min_length=6,  max_length=72)
    role:     str       = Field("citizen", pattern="^(citizen|officer|admin)$")
    address:  Optional[str] = None
    state:    Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name":     "Ram Kumar",
                "email":    "ram.kumar@example.com",
                "phone":    "9876543210",
                "password": "securepass123",
                "role":     "citizen",
                "address":  "Village Rampur, District Varanasi",
                "state":    "Uttar Pradesh"
            }
        }
    }


class UserLogin(BaseModel):
    """Request body for login."""
    email:    EmailStr
    password: str = Field(..., min_length=6,max_length=72)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email":    "ram.kumar@example.com",
                "password": "securepass123"
            }
        }
    }


class UserResponse(BaseModel):
    """Response after login or get current user."""
    id:         str
    name:       str
    email:      str
    phone:      Optional[str]
    role:       str
    state:      Optional[str]
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Request body for updating current user's profile."""
    name:    Optional[str] = Field(None, min_length=2, max_length=100)
    phone:   Optional[str] = Field(None, max_length=15)
    address: Optional[str] = None
    state:   Optional[str] = None


class TokenResponse(BaseModel):
    """Response after successful login."""
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


# ─── Document Schemas ─────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Response for uploaded document details."""
    id:                  str
    doc_type:            str
    file_url:            Optional[str]
    certificate_number:  Optional[str]
    verification_status: str
    extracted_data:      Optional[str]
    uploaded_at:         datetime

    model_config = {"from_attributes": True}


# ─── Citizen Schemas ──────────────────────────────────────────

class ApplicationCreate(BaseModel):
    """
    Request body for submitting a new NSAP application.
    Fields match the CatBoost model training features exactly.
    """
    age:                   int = Field(..., ge=18,  le=120)
    gender:                str = Field(..., pattern="^(Male|Female|Other)$")
    marital_status:        str
    annual_income:         int = Field(..., ge=0)
    bpl_card:              str = Field(..., pattern="^(Yes|No)$")
    area_type:             str = Field(..., pattern="^(Rural|Urban)$")
    state:                 str
    social_category:       str
    employment_status:     str
    has_disability:        str = Field(..., pattern="^(Yes|No)$")
    disability_percentage: int = Field(0,   ge=0, le=100)
    disability_type:       str = "None"
    aadhaar_linked:        str = Field(..., pattern="^(Yes|No)$")
    bank_account:          str = Field(..., pattern="^(Yes|No)$")

    model_config = {
        "json_schema_extra": {
            "example": {
                "age":                   68,
                "gender":                "Female",
                "marital_status":        "Widowed",
                "annual_income":         35000,
                "bpl_card":              "Yes",
                "area_type":             "Rural",
                "state":                 "Uttar Pradesh",
                "social_category":       "SC",
                "employment_status":     "Unemployed",
                "has_disability":        "No",
                "disability_percentage": 0,
                "disability_type":       "None",
                "aadhaar_linked":        "Yes",
                "bank_account":          "Yes"
            }
        }
    }


class PredictionDetail(BaseModel):
    """Nested prediction details inside application response."""
    predicted_scheme:  str
    confidence_score:  float
    all_probabilities: Optional[Dict[str, float]]
    needs_review:      bool
    created_at:        datetime

    model_config = {"from_attributes": True}


class ApplicationResponse(BaseModel):
    """Response after submitting application — includes prediction."""
    id:                    str
    status:                str
    age:                   int
    gender:                str
    marital_status:        str
    annual_income:         int
    bpl_card:              str
    area_type:             str
    state:                 str
    social_category:       str
    employment_status:     str
    has_disability:        str
    disability_percentage: int
    disability_type:       str
    aadhaar_linked:        str
    bank_account:          str
    submitted_at:          datetime
    prediction:            Optional[PredictionDetail]
    documents:             Optional[List[DocumentResponse]]

    model_config = {"from_attributes": True}


class ApplicationSummary(BaseModel):
    """Lightweight application summary for list views."""
    id:               str
    status:           str
    submitted_at:     datetime
    predicted_scheme: Optional[str]
    confidence_score: Optional[float]
    needs_review:     Optional[bool]
    state:            str
    gender:           str
    age:              int

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    """Response for citizen notifications."""
    id:             str
    message:        str
    is_read:        bool
    created_at:     datetime
    application_id: Optional[str]

    model_config = {"from_attributes": True}


# ─── Officer Schemas ──────────────────────────────────────────

class DecisionCreate(BaseModel):
    """Request body for officer approve/reject decision."""
    application_id:  str
    decision:        str = Field(..., pattern="^(approved|rejected)$")
    remarks:         Optional[str] = Field(None, max_length=500)
    override_scheme: Optional[str] = Field(
        None,
        pattern="^(OAP|WP|DP|NOT_ELIGIBLE)$"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "application_id":  "uuid-here",
                "decision":        "approved",
                "remarks":         "Documents verified. Applicant qualifies for OAP.",
                "override_scheme": None
            }
        }
    }


class DecisionResponse(BaseModel):
    """Response after officer makes a decision."""
    id:              str
    application_id:  str
    officer_id:      str
    decision:        str
    remarks:         Optional[str]
    override_scheme: Optional[str]
    decided_at:      datetime

    model_config = {"from_attributes": True}


class OfficerApplicationDetail(BaseModel):
    """
    Full application detail for officer review.
    Includes prediction, SHAP values, documents and citizen info.
    """
    id:                    str
    status:                str
    submitted_at:          datetime
    age:                   int
    gender:                str
    marital_status:        str
    annual_income:         int
    bpl_card:              str
    area_type:             str
    state:                 str
    social_category:       str
    employment_status:     str
    has_disability:        str
    disability_percentage: int
    disability_type:       str
    aadhaar_linked:        str
    bank_account:          str
    citizen:               Optional[UserResponse]
    prediction:            Optional[PredictionDetail]
    documents:             Optional[List[DocumentResponse]]
    decision:              Optional[DecisionResponse]

    model_config = {"from_attributes": True}


# ─── Admin Schemas ────────────────────────────────────────────

class SchemeStats(BaseModel):
    """Per scheme application counts."""
    OAP:          int
    WP:           int
    DP:           int
    NOT_ELIGIBLE: int


class StatusStats(BaseModel):
    """Application counts by status."""
    pending:       int
    auto_approved: int
    needs_review:  int
    approved:      int
    rejected:      int


class AdminDashboardStats(BaseModel):
    """
    Full admin dashboard statistics response.
    Includes application stats, model metrics and officer activity.
    """
    # Application counts
    total_applications: int
    by_status:          StatusStats
    by_scheme:          SchemeStats

    # Model performance
    model_accuracy:     float
    model_f1_weighted:  float
    avg_confidence:     float
    needs_review_count: int
    needs_review_pct:   float

    # Officer activity
    total_officers:     int
    decisions_today:    int
    avg_decision_time_hrs: Optional[float]


class ModelMetrics(BaseModel):
    """
    Model evaluation metrics for admin dashboard.
    Loaded from ml/model_comparison.csv
    """
    model_name:    str
    accuracy:      float
    precision:     float
    recall:        float
    f1_weighted:   float
    f1_dp:         float
    f1_not_eligible: float
    f1_oap:        float
    f1_wp:         float


class FairnessEntry(BaseModel):
    """
    Single row from fairness report.
    Loaded from ml/fairness_report.csv
    """
    group_column:              str
    group:                     str
    count:                     int
    not_eligible_rate:         float
    error_rate:                float
    false_not_eligible_rate:   float
    false_eligible_rate:       float
    flag:                      str


class OfficerActivity(BaseModel):
    """Officer performance summary for admin."""
    officer_id:      str
    officer_name:    str
    total_decisions: int
    approved:        int
    rejected:        int
    overrides:       int