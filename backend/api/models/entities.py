"""
Module: api/models/entities.py
Description: SQLAlchemy ORM table definitions for NSAP Classification System.
             Defines all 6 database tables:
             - User (citizens, officers, admins)
             - Application (applicant submissions)
             - Document (uploaded files + OCR results)
             - Prediction (model inference results)
             - Decision (officer approve/reject)
             - Notification (citizen status updates)
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float,
    Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship

from api.models.database import Base


def generate_uuid():
    """Generate a new UUID4 string for use as primary key."""
    return str(uuid.uuid4())


# ─── User ─────────────────────────────────────────────────────
class User(Base):
    """
    Stores all system users — citizens, officers and admins.
    Role determines which endpoints the user can access.
    """
    __tablename__ = "users"

    id            = Column(String(36),  primary_key=True, default=generate_uuid)
    name          = Column(String(100), nullable=False)
    email         = Column(String(100), nullable=False, unique=True, index=True)
    phone         = Column(String(15),  nullable=True)
    password_hash = Column(String(255), nullable=False)

    # Role: citizen | officer | admin
    role          = Column(String(20),  nullable=False, default="citizen")
    is_active     = Column(Boolean,     default=True)

    # Address fields (mainly for citizens)
    address       = Column(Text,        nullable=True)
    state         = Column(String(50),  nullable=True)

    created_at    = Column(DateTime,    default=datetime.now)
    updated_at    = Column(DateTime,    default=datetime.now, onupdate=datetime.now)

    # Relationships
    applications  = relationship("Application", back_populates="citizen",
                                  foreign_keys="Application.citizen_id")
    decisions     = relationship("Decision",    back_populates="officer",
                                  foreign_keys="Decision.officer_id")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ─── Application ──────────────────────────────────────────────
class Application(Base):
    """
    Stores each citizen's NSAP scheme application.
    Links to prediction result, uploaded documents,
    officer decision and notifications.
    """
    __tablename__ = "applications"

    id          = Column(String(36), primary_key=True, default=generate_uuid)
    citizen_id  = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # ── Applicant form fields ──────────────────────────────────
    age                   = Column(Integer,     nullable=False)
    gender                = Column(String(10),  nullable=False)
    marital_status        = Column(String(20),  nullable=False)
    annual_income         = Column(Integer,     nullable=False)
    bpl_card              = Column(String(5),   nullable=False)
    area_type             = Column(String(10),  nullable=False)
    state                 = Column(String(50),  nullable=False)
    social_category       = Column(String(20),  nullable=False)
    employment_status     = Column(String(30),  nullable=False)
    has_disability        = Column(String(5),   nullable=False)
    disability_percentage = Column(Integer,     default=0)
    disability_type       = Column(String(50),  default="None")
    aadhaar_linked        = Column(String(5),   nullable=False)
    bank_account          = Column(String(5),   nullable=False)

    # ── Application status ────────────────────────────────────
    # pending | auto_approved | needs_review | approved | rejected
    status      = Column(String(20), default="pending", index=True)

    # Officer assigned for review (nullable until assigned)
    officer_id  = Column(String(36), ForeignKey("users.id"), nullable=True)

    submitted_at = Column(DateTime, default=datetime.now)
    updated_at   = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    citizen      = relationship("User",         back_populates="applications",
                                 foreign_keys=[citizen_id])
    officer      = relationship("User",         foreign_keys=[officer_id])
    prediction   = relationship("Prediction",   back_populates="application",
                                 uselist=False)
    documents    = relationship("Document",     back_populates="application")
    decision     = relationship("Decision",     back_populates="application",
                                 uselist=False)
    notifications = relationship("Notification", back_populates="application")

    def __repr__(self):
        return f"<Application {self.id} — {self.status}>"


# ─── Document ─────────────────────────────────────────────────
class Document(Base):
    """
    Stores uploaded documents for each application.
    Tracks OCR extraction results and mock verification status.
    """
    __tablename__ = "documents"

    id             = Column(String(36),  primary_key=True, default=generate_uuid)
    application_id = Column(String(36),  ForeignKey("applications.id"),
                            nullable=False, index=True)

    # Document classification
    # aadhaar | bpl_card | disability_certificate | death_certificate
    doc_type       = Column(String(30),  nullable=False)

    # Cloudinary URL for stored document image
    file_url       = Column(String(500), nullable=True)

    # Raw OCR text (first 1000 chars for debugging)
    ocr_raw_text   = Column(Text,        nullable=True)

    # JSON string of fields extracted by OCR
    # e.g. {"age": 65, "gender": "Male", "state": "Bihar"}
    extracted_data = Column(Text,        nullable=True)

    # Certificate number extracted for mock verification
    certificate_number = Column(String(100), nullable=True)

    # pending | verified | failed
    verification_status = Column(String(20), default="pending")

    uploaded_at    = Column(DateTime,    default=datetime.now)

    # Relationships
    application    = relationship("Application", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.doc_type} — {self.verification_status}>"


# ─── Prediction ───────────────────────────────────────────────
class Prediction(Base):
    """
    Stores CatBoost model inference results for each application.
    Kept separate from Application for clean data separation.
    """
    __tablename__ = "predictions"

    id             = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"),
                            nullable=False, unique=True, index=True)

    # Model output
    predicted_scheme   = Column(String(20),  nullable=False)
    confidence_score   = Column(Float,       nullable=False)

    # JSON string of all class probabilities
    # e.g. {"OAP": 0.87, "WP": 0.05, "DP": 0.03, "NOT_ELIGIBLE": 0.05}
    all_probabilities  = Column(Text,        nullable=True)

    # True if confidence < CONF_THRESHOLD (0.85)
    # → placed in priority officer review queue
    needs_review       = Column(Boolean,     default=False)

    # JSON string of SHAP values for explainability
    shap_values        = Column(Text,        nullable=True)

    created_at         = Column(DateTime,    default=datetime.now)

    # Relationships
    application        = relationship("Application", back_populates="prediction")

    def __repr__(self):
        return f"<Prediction {self.predicted_scheme} ({self.confidence_score:.2f})>"


# ─── Decision ─────────────────────────────────────────────────
class Decision(Base):
    """
    Stores officer approve/reject decisions for applications.
    Officer can override the model's predicted scheme if needed.
    """
    __tablename__ = "decisions"

    id             = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"),
                            nullable=False, unique=True, index=True)
    officer_id     = Column(String(36), ForeignKey("users.id"),
                            nullable=False)

    # approved | rejected
    decision       = Column(String(20), nullable=False)

    # Officer remarks explaining the decision
    remarks        = Column(Text,       nullable=True)

    # If officer overrides model prediction, store the corrected scheme
    # NULL means officer agreed with model prediction
    override_scheme = Column(String(20), nullable=True)

    decided_at     = Column(DateTime,   default=datetime.now)

    # Relationships
    application    = relationship("Application", back_populates="decision")
    officer        = relationship("User",        back_populates="decisions",
                                   foreign_keys=[officer_id])

    def __repr__(self):
        return f"<Decision {self.decision} by officer {self.officer_id}>"


# ─── Notification ─────────────────────────────────────────────
class Notification(Base):
    """
    Stores status update notifications for citizens.
    Created automatically when application status changes.
    """
    __tablename__ = "notifications"

    id             = Column(String(36),  primary_key=True, default=generate_uuid)
    user_id        = Column(String(36),  ForeignKey("users.id"),
                            nullable=False, index=True)
    application_id = Column(String(36),  ForeignKey("applications.id"),
                            nullable=True)

    # Notification message shown to citizen
    message        = Column(Text,        nullable=False)

    # False until citizen views the notification
    is_read        = Column(Boolean,     default=False)

    created_at     = Column(DateTime,    default=datetime.now)

    # Relationships
    user           = relationship("User",        back_populates="notifications")
    application    = relationship("Application", back_populates="notifications")

    def __repr__(self):
        return f"<Notification user={self.user_id} read={self.is_read}>"