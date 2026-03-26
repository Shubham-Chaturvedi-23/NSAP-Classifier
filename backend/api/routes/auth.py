"""
Module: api/routes/auth.py
Description: Authentication endpoints for all user roles.
             Handles registration, login and current user retrieval.
             Uses JWT tokens for stateless authentication.
             Passwords are hashed using bcrypt via passlib.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.models.database import get_db
from api.models.entities import User
from api.models.schemas import (
    UserRegister, UserLogin,
    UserResponse, TokenResponse,
    UserProfileUpdate,
)
from api.config import (
    SECRET_KEY, JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES, UserRole,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── Security Setup ───────────────────────────────────────────
# bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme — token extracted from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form")


# ─── Password Helpers ─────────────────────────────────────────
def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Bcrypt hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Args:
        plain  (str): Plain text password from login request.
        hashed (str): Stored bcrypt hash from database.

    Returns:
        bool: True if password matches.
    """
    return pwd_context.verify(plain, hashed)


# ─── JWT Helpers ──────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    Args:
        data (dict): Payload to encode — typically {"sub": user_id,
                     "role": user_role, "email": user_email}

    Returns:
        str: Signed JWT token string.
    """
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Args:
        token (str): JWT token string.

    Returns:
        dict: Decoded payload.

    Raises:
        HTTPException 401: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid or expired token.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )


# ─── Current User Dependencies ────────────────────────────────
def get_current_user(
    token: str     = Depends(oauth2_scheme),
    db:    Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — extract and validate current user from JWT.
    Use in any protected route via Depends(get_current_user).

    Args:
        token (str):     JWT token from Authorization header.
        db    (Session): Database session.

    Returns:
        User: Current authenticated user ORM object.

    Raises:
        HTTPException 401: If token invalid or user not found.
        HTTPException 403: If user account is deactivated.
    """
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid token payload.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Account deactivated. Contact administrator.",
        )

    return user


def require_citizen(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency — ensure current user has citizen role.

    Raises:
        HTTPException 403: If user is not a citizen.
    """
    if current_user.role != UserRole.CITIZEN:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Citizen access required.",
        )
    return current_user


def require_officer(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency — ensure current user has officer role.

    Raises:
        HTTPException 403: If user is not an officer.
    """
    if current_user.role != UserRole.OFFICER:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Officer access required.",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency — ensure current user has admin role.

    Raises:
        HTTPException 403: If user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Admin access required.",
        )
    return current_user


# ─── Endpoints ────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    POST /api/v1/auth/register

    Register a new user account.
    Default role is citizen unless specified.

    Flow:
        1. Check email not already registered
        2. Hash password
        3. Create user record
        4. Return user details (no token — must login separately)

    Raises:
        HTTPException 400: If email already registered.
    """
    # Check email uniqueness
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Email already registered.",
        )

    # Create new user
    user = User(
        name          = data.name,
        email         = data.email,
        phone         = data.phone,
        password_hash = hash_password(data.password),
        role          = data.role,
        address       = data.address,
        state         = data.state,
        is_active     = True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    POST /api/v1/auth/login

    Login with email and password.
    Returns JWT access token and user details.

    Flow:
        1. Find user by email
        2. Verify password
        3. Generate JWT token
        4. Return token + user info

    Raises:
        HTTPException 401: If credentials are invalid.
        HTTPException 403: If account is deactivated.
    """
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()

    # Verify credentials
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Account deactivated. Contact administrator.",
        )

    # Generate JWT token
    token = create_access_token({
        "sub":   user.id,
        "role":  user.role,
        "email": user.email,
    })

    return TokenResponse(
        access_token = token,
        token_type   = "bearer",
        user         = user,
    )


@router.post("/login/form", response_model=TokenResponse)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session                   = Depends(get_db),
):
    """
    POST /api/v1/auth/login/form

    OAuth2 compatible login for Swagger UI testing.
    Uses form fields (username = email) instead of JSON body.
    """
    user = db.query(User).filter(User.email == form.username).first()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid email or password.",
        )

    token = create_access_token({
        "sub":   user.id,
        "role":  user.role,
        "email": user.email,
    })

    return TokenResponse(
        access_token = token,
        token_type   = "bearer",
        user         = user,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    GET /api/v1/auth/me

    Return current authenticated user's profile.
    Requires valid JWT token in Authorization header.

    Returns:
        UserResponse: Current user details.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    data: UserProfileUpdate,
    current_user: User    = Depends(get_current_user),
    db:      Session       = Depends(get_db),
):
    """
    PUT /api/v1/auth/me

    Update current user's profile details.
    Only name, phone, address and state can be updated.

    Returns:
        UserResponse: Updated user details.
    """
    if data.name is not None:
        current_user.name = data.name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.address is not None:
        current_user.address = data.address
    if data.state is not None:
        current_user.state = data.state

    db.commit()
    db.refresh(current_user)
    return current_user