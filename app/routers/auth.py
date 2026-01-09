"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.schemas import (
    GoogleAuthRequest,
    AuthResponse,
    RefreshTokenRequest,
    TokenResponse,
    ValidateResponse,
    StandardResponse,
    ErrorResponse,
    UserResponse
)
from app.services.auth_service import auth_service
from app.middleware.auth_middleware import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def set_auth_cookie(response: Response, token: str):
    """
    Set secure auth cookie

    Args:
        response: FastAPI Response object
        token: JWT token to set
    """
    max_age = settings.jwt_expiration_days * 24 * 60 * 60  # Convert days to seconds

    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=settings.is_production,  # Only HTTPS in production
        samesite="strict",
        max_age=max_age
    )


@router.post("/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def google_auth(
    request: GoogleAuthRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth (Firebase)

    - Verifies Firebase ID token
    - Creates or updates user in database
    - Generates JWT token
    - Sets secure cookie
    """
    try:
        result = auth_service.authenticate_with_google(
            db=db,
            id_token=request.idToken,
            email=request.email,
            display_name=request.displayName,
            photo_url=request.photoURL,
            uid=request.uid
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )

        jwt_token, user = result

        # Set auth cookie
        set_auth_cookie(response, jwt_token)

        return AuthResponse(
            success=True,
            token=jwt_token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                photoURL=user.get("photoURL")
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in google_auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    Logout user

    - Clears auth cookie
    - Requires authentication
    """
    try:
        # Clear the auth cookie
        response.delete_cookie(key="auth_token")

        return StandardResponse(
            success=True,
            message="Sesión cerrada correctamente"
        )

    except Exception as e:
        logger.error(f"Error in logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh JWT token using new Firebase token

    - Verifies new Firebase token
    - Generates new JWT token
    - Updates auth cookie
    """
    try:
        result = auth_service.refresh_token(db=db, id_token=request.idToken)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        jwt_token, user = result

        # Set new auth cookie
        set_auth_cookie(response, jwt_token)

        return TokenResponse(
            success=True,
            token=jwt_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/validate", response_model=ValidateResponse, status_code=status.HTTP_200_OK)
async def validate_token(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate current JWT token

    - Checks if token is valid
    - Returns user information
    - Requires authentication
    """
    try:
        return ValidateResponse(
            success=True,
            valid=True,
            user=UserResponse(
                id=current_user["id"],
                email=current_user["email"],
                name=current_user.get("name", ""),
                photoURL=current_user.get("photoURL")
            )
        )

    except Exception as e:
        logger.error(f"Error in validate_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
