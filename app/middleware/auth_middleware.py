"""
Authentication middleware and dependencies
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.jwt_service import jwt_service

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll check cookies too


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get current authenticated user

    Tries to get token from:
    1. Authorization header (Bearer token)
    2. Cookie (auth_token)

    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session

    Returns:
        User dict with id, firebase_uid, email

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = None
    token_source = None

    # Log request details
    logger.info(f"🔐 Auth check for: {request.method} {request.url.path}")
    logger.info(f"📨 Headers: {dict(request.headers)}")
    logger.info(f"🍪 Cookies: {dict(request.cookies)}")

    # Try to get token from Authorization header
    if credentials:
        token = credentials.credentials
        token_source = "Authorization header"
        logger.info(f"✅ Token found in Authorization header: {token[:20]}...")
    # Try to get token from cookie
    elif "auth_token" in request.cookies:
        token = request.cookies["auth_token"]
        token_source = "Cookie"
        logger.info(f"✅ Token found in Cookie: {token[:20]}...")
    else:
        logger.warning(f"❌ No token found in request")
        logger.warning(f"   - Authorization header: {request.headers.get('Authorization', 'Not present')}")
        logger.warning(f"   - Cookies: {list(request.cookies.keys())}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - No token found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    logger.info(f"🔍 Verifying token from {token_source}...")
    payload = jwt_service.verify_token(token)

    if not payload:
        logger.error(f"❌ Token verification failed for token from {token_source}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"✅ Token verified successfully. Payload: {payload}")

    # Extract user info from token
    user_id = payload.get("user_id")
    firebase_uid = payload.get("firebase_uid")
    email = payload.get("email")

    if not user_id or not firebase_uid or not email:
        logger.error(f"❌ Invalid token payload. Missing fields: user_id={user_id}, firebase_uid={firebase_uid}, email={email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    logger.info(f"✅ User authenticated: {email} (ID: {user_id})")

    return {
        "id": user_id,
        "firebase_uid": firebase_uid,
        "email": email
    }


def optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Optional authentication dependency

    Returns user dict if authenticated, None otherwise
    Does not raise exceptions
    """
    token = None

    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    # Try to get token from cookie
    elif "auth_token" in request.cookies:
        token = request.cookies["auth_token"]

    if not token:
        return None

    # Verify token
    payload = jwt_service.verify_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    firebase_uid = payload.get("firebase_uid")
    email = payload.get("email")

    if not user_id or not firebase_uid or not email:
        return None

    return {
        "id": user_id,
        "firebase_uid": firebase_uid,
        "email": email
    }
