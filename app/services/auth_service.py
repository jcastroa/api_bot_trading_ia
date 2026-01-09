"""
Authentication service combining Firebase and JWT
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Tuple
from datetime import datetime
import logging

from app.services.firebase_service import firebase_service
from app.services.jwt_service import jwt_service

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""

    def authenticate_with_google(
        self,
        db: Session,
        id_token: str,
        email: str,
        display_name: str,
        photo_url: Optional[str],
        uid: str
    ) -> Optional[Tuple[str, dict]]:
        """
        Authenticate user with Google/Firebase

        Args:
            db: Database session
            id_token: Firebase ID token
            email: User email
            display_name: User display name
            photo_url: User photo URL
            uid: Firebase UID

        Returns:
            Tuple of (jwt_token, user_dict) if successful, None if failed
        """
        # Verify Firebase token
        decoded_token = firebase_service.verify_id_token(id_token)
        if not decoded_token:
            logger.warning("Invalid Firebase token")
            return None

        # Verify UID matches
        if decoded_token.get("uid") != uid:
            logger.warning("UID mismatch")
            return None

        # Find or create user in database
        user = self._find_or_create_user(db, uid, email, display_name, photo_url)
        if not user:
            logger.error("Failed to create/find user")
            return None

        # Generate JWT token
        jwt_token = jwt_service.create_access_token(
            user_id=user["id"],
            firebase_uid=user["firebase_uid"],
            email=user["email"]
        )

        return jwt_token, user

    def refresh_token(self, db: Session, id_token: str) -> Optional[Tuple[str, dict]]:
        """
        Refresh JWT token using new Firebase token

        Args:
            db: Database session
            id_token: New Firebase ID token

        Returns:
            Tuple of (jwt_token, user_dict) if successful, None if failed
        """
        # Verify Firebase token
        decoded_token = firebase_service.verify_id_token(id_token)
        if not decoded_token:
            return None

        uid = decoded_token.get("uid")
        if not uid:
            return None

        # Find user by Firebase UID
        user = self._find_user_by_firebase_uid(db, uid)
        if not user:
            return None

        # Generate new JWT token
        jwt_token = jwt_service.create_access_token(
            user_id=user["id"],
            firebase_uid=user["firebase_uid"],
            email=user["email"]
        )

        return jwt_token, user

    def validate_jwt_token(self, db: Session, token: str) -> Optional[dict]:
        """
        Validate JWT token and return user data

        Args:
            db: Database session
            token: JWT token

        Returns:
            User dict if valid, None if invalid
        """
        payload = jwt_service.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        # Get user from database
        user = self._find_user_by_id(db, user_id)
        return user

    def _find_or_create_user(
        self,
        db: Session,
        firebase_uid: str,
        email: str,
        name: str,
        photo_url: Optional[str]
    ) -> Optional[dict]:
        """Find existing user or create new one"""
        try:
            # Check if user exists
            result = db.execute(
                text("""
                    SELECT id, firebase_uid, email, name, photo_url, created_at
                    FROM users
                    WHERE firebase_uid = :firebase_uid
                """),
                {"firebase_uid": firebase_uid}
            ).fetchone()

            if result:
                # User exists, update info
                db.execute(
                    text("""
                        UPDATE users
                        SET email = :email, name = :name, photo_url = :photo_url, last_login = NOW()
                        WHERE firebase_uid = :firebase_uid
                    """),
                    {
                        "firebase_uid": firebase_uid,
                        "email": email,
                        "name": name,
                        "photo_url": photo_url
                    }
                )
                db.commit()

                return {
                    "id": result[0],
                    "firebase_uid": result[1],
                    "email": email,
                    "name": name,
                    "photoURL": photo_url
                }
            else:
                # Create new user
                result = db.execute(
                    text("""
                        INSERT INTO users (firebase_uid, email, name, photo_url, created_at, last_login)
                        VALUES (:firebase_uid, :email, :name, :photo_url, NOW(), NOW())
                    """),
                    {
                        "firebase_uid": firebase_uid,
                        "email": email,
                        "name": name,
                        "photo_url": photo_url
                    }
                )
                db.commit()

                # Get the newly created user ID
                user_id = result.lastrowid

                return {
                    "id": user_id,
                    "firebase_uid": firebase_uid,
                    "email": email,
                    "name": name,
                    "photoURL": photo_url
                }

        except Exception as e:
            logger.error(f"Error in _find_or_create_user: {e}")
            db.rollback()
            return None

    def _find_user_by_firebase_uid(self, db: Session, firebase_uid: str) -> Optional[dict]:
        """Find user by Firebase UID"""
        try:
            result = db.execute(
                text("""
                    SELECT id, firebase_uid, email, name, photo_url
                    FROM users
                    WHERE firebase_uid = :firebase_uid
                """),
                {"firebase_uid": firebase_uid}
            ).fetchone()

            if result:
                return {
                    "id": result[0],
                    "firebase_uid": result[1],
                    "email": result[2],
                    "name": result[3],
                    "photoURL": result[4]
                }
            return None

        except Exception as e:
            logger.error(f"Error in _find_user_by_firebase_uid: {e}")
            return None

    def _find_user_by_id(self, db: Session, user_id: int) -> Optional[dict]:
        """Find user by ID"""
        try:
            result = db.execute(
                text("""
                    SELECT id, firebase_uid, email, name, photo_url
                    FROM users
                    WHERE id = :user_id
                """),
                {"user_id": user_id}
            ).fetchone()

            if result:
                return {
                    "id": result[0],
                    "firebaseUid": result[1],
                    "email": result[2],
                    "name": result[3],
                    "photoURL": result[4]
                }
            return None

        except Exception as e:
            logger.error(f"Error in _find_user_by_id: {e}")
            return None


# Global instance
auth_service = AuthService()
