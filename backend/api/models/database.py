"""
Module: api/models/database.py
Description: SQLAlchemy engine, session factory and base class setup.
             Provides get_db() dependency for FastAPI route injection
             and create_tables() called once on application startup.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from api.config import DATABASE_URL

# ─── Engine ───────────────────────────────────────────────────
# pool_pre_ping — test connection before using from pool
# pool_recycle  — recycle connections after 1 hour (prevents stale connections)
# echo          — set True to log all SQL queries (useful for debugging)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping = True,
    pool_recycle  = 3600,
    echo          = False,
)

# ─── Session Factory ──────────────────────────────────────────
# autocommit=False — we manually commit transactions
# autoflush=False  — we manually flush before queries
SessionLocal = sessionmaker(
    autocommit = False,
    autoflush  = False,
    bind       = engine,
)

# ─── Base Class ───────────────────────────────────────────────
# All ORM models in entities.py inherit from this Base.
# Required for create_all() to discover and create tables.
Base = declarative_base()


# ─── Table Creation ───────────────────────────────────────────
def create_tables():
    """
    Create all database tables if they do not already exist.
    Called once during FastAPI application startup in app.py lifespan.
    Safe to call multiple times — skips existing tables.
    """
    # Import entities here to ensure all models are registered
    # with Base.metadata before create_all() is called.
    from api.models import entities  # noqa: F401
    Base.metadata.create_all(bind=engine)


# ─── Database Dependency ──────────────────────────────────────
def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Automatically closes session after request completes.

    Usage in routes:
        from api.models.database import get_db
        from sqlalchemy.orm import Session

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()