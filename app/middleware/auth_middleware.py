"""
Authentication middleware and dependencies
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.jwt_service import jwt_service

security = HTTPBearer()


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

    # Try to get token from Authorization header
    if credentials:
        token = credentials.credentials
    # Try to get token from cookie
    elif "auth_token" in request.cookies:
        token = request.cookies["auth_token"]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    payload = jwt_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_id = payload.get("user_id")
    firebase_uid = payload.get("firebase_uid")
    email = payload.get("email")

    if not user_id or not firebase_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

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
