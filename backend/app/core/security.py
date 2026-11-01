import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# Argon2id password hasher with secure RFC 9106 default parameters
_password_hasher = PasswordHasher()

ACCESS_TOKEN_TYPE = "access"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
DEFAULT_JWT_ALGORITHM = settings.JWT_ALGORITHM


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id with a cryptographically secure random salt.

    Args:
        password: The plaintext password string to hash.

    Returns:
        The Argon2id hash string.

    Raises:
        ValueError: If the password is empty or not a string.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against an Argon2id hash.
    Safely handles malformed hashes, mismatched credentials, or corrupted values without throwing.

    Args:
        plain_password: The plaintext candidate password.
        hashed_password: The stored Argon2id hash.

    Returns:
        True if the password matches the hash; False otherwise.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError, ValueError):
        return False
    except Exception:
        # Fallback safeguard against unexpected formatting or binary decode errors
        return False


def create_access_token(
    subject: str,
    secret_key: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    algorithm: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Creates a signed JWT access token containing subject, issued-at, expiration, and token type.

    Args:
        subject: The unique user identifier (stored in 'sub' claim as a string).
        secret_key: Optional cryptographic key. If omitted, retrieves settings.get_jwt_secret_key().
        expires_delta: Optional custom duration until expiration. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.
        algorithm: Optional HMAC algorithm. Defaults to settings.JWT_ALGORITHM.
        extra_claims: Optional dictionary of additional claims to embed in the payload.

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: If subject is empty or effective secret_key is blank.
        RuntimeError: If secret_key is omitted and JWT_SECRET_KEY is unconfigured in settings.
    """
    if not subject or not str(subject).strip():
        raise ValueError("Subject 'sub' must be a non-empty string.")

    effective_secret = secret_key if secret_key is not None else settings.get_jwt_secret_key()
    if not effective_secret or not effective_secret.strip():
        raise ValueError("JWT signing secret key must be provided.")

    effective_algorithm = algorithm or settings.JWT_ALGORITHM
    effective_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=effective_expire_minutes)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": ACCESS_TOKEN_TYPE,
    }

    if extra_claims:
        # Prevent callers from accidentally overwriting critical security claims
        filtered_extra = {
            k: v for k, v in extra_claims.items() if k not in ("sub", "iat", "exp", "type")
        }
        payload.update(filtered_extra)

    return jwt.encode(payload, effective_secret, algorithm=effective_algorithm)


def decode_access_token(
    token: str,
    secret_key: Optional[str] = None,
    algorithms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Decodes and cryptographically validates a JWT access token.

    Validates:
        1. Token signature against the effective secret key.
        2. Token expiration ('exp') claim using timezone-aware UTC.
        3. Token issued-at ('iat') claim.
        4. Presence and validity of subject ('sub') claim.
        5. Token type claim matching 'access'.
        6. Explicitly restricted algorithms (never trusts arbitrary header-specified algorithms).

    Args:
        token: The encoded JWT string.
        secret_key: Optional cryptographic key. If omitted, retrieves settings.get_jwt_secret_key().
        algorithms: Explicit list of allowed algorithms. Defaults to [settings.JWT_ALGORITHM].

    Returns:
        Decoded payload dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidSignatureError: If the signature is invalid or tampered.
        jwt.DecodeError: If the token structure is malformed.
        jwt.InvalidTokenError: If subject is missing, type is invalid, or claims are invalid.
        ValueError: If effective secret_key is blank.
        RuntimeError: If secret_key is omitted and JWT_SECRET_KEY is unconfigured in settings.
    """
    if not token or not isinstance(token, str):
        raise jwt.DecodeError("Token must be a valid non-empty string.")

    effective_secret = secret_key if secret_key is not None else settings.get_jwt_secret_key()
    if not effective_secret or not effective_secret.strip():
        raise ValueError("JWT secret key must be provided for verification.")

    allowed_algorithms = algorithms if algorithms is not None else [settings.JWT_ALGORITHM]

    # Explicitly enforce algorithm restriction and required claims
    payload = jwt.decode(
        token,
        effective_secret,
        algorithms=allowed_algorithms,
        options={
            "require": ["exp", "iat", "sub"],
            "verify_exp": True,
            "verify_iat": True,
            "verify_signature": True,
        },
    )

    subject = payload.get("sub")
    if subject is None or not str(subject).strip():
        raise jwt.InvalidTokenError("Token subject claim 'sub' is missing or empty.")

    token_type = payload.get("type")
    if token_type != ACCESS_TOKEN_TYPE:
        raise jwt.InvalidTokenError(
            f"Invalid token type: expected '{ACCESS_TOKEN_TYPE}', received '{token_type}'."
        )

    return payload
