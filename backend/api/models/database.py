"""
api/database.py
===============
SQLAlchemy database models and session management.
"""

from sqlalchemy import (
    create_engine, Column, String, Integer,
    Float, Boolean, DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


class Application(Base):
    """Stores each applicant submission, model prediction and officer decision."""
    __tablename__ = "applications"

    # Identity
    id           = Column(String(36), primary_key=True,
                          default=lambda: str(uuid.uuid4()))
    submitted_at = Column(DateTime, default=datetime.now)

    # Applicant features
    age                   = Column(Integer)
    gender                = Column(String(10))
    marital_status        = Column(String(20))
    annual_income         = Column(Integer)
    bpl_card              = Column(String(5))
    area_type             = Column(String(10))
    state                 = Column(String(50))
    social_category       = Column(String(20))
    employment_status     = Column(String(30))
    has_disability        = Column(String(5))
    disability_percentage = Column(Integer)
    disability_type       = Column(String(50))
    aadhaar_linked        = Column(String(5))
    bank_account          = Column(String(5))

    # OCR extracted document names
    documents_uploaded    = Column(Text, nullable=True)

    # Model output
    predicted_scheme      = Column(String(20))
    confidence            = Column(Float)
    all_qualifying        = Column(Text)
    needs_review          = Column(Boolean, default=False)

    # Officer decision
    status       = Column(String(20), default="PENDING")
    officer_note = Column(Text, nullable=True)
    decided_at   = Column(DateTime, nullable=True)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
