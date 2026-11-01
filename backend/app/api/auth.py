import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.db_models import User
from app.models.schemas import UserCreate, UserLogin, UserResponse, AuthResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user account.
    Normalizes email, checks case-insensitively for duplicates, hashes password using Argon2id,
    persists the user, and returns an access JWT along with public user details.
    """
    normalized_email = request.email.strip().lower()

    # Pre-check for existing account with case insensitivity
    existing = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed_pw = hash_password(request.password)

    new_user = User(
        email=normalized_email,
        hashed_password=hashed_pw,
        full_name=request.full_name,
        is_active=True,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully: id={new_user.id}")
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    access_token = create_access_token(subject=str(new_user.id))

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=AuthResponse)
def login(request: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user by email and password.
    Returns a generic 401 response on any authentication failure to prevent user enumeration.
    """
    invalid_credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    normalized_email = request.email.strip().lower()

    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if not user:
        raise invalid_credentials_exc

    if not verify_password(request.password, user.hashed_password):
        raise invalid_credentials_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns public profile information for the authenticated user.
    """
    return UserResponse.model_validate(current_user)

