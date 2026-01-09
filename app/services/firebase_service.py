"""
Firebase service for token verification
"""
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional, Dict
import json
import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for Firebase authentication operations"""

    def __init__(self):
        self._initialized = False
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self._initialized = True
                logger.info("Firebase already initialized")
                return

            # Try to load credentials from file first
            if settings.firebase_credentials_path and os.path.exists(settings.firebase_credentials_path):
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info(f"Firebase initialized from file: {settings.firebase_credentials_path}")
                self._initialized = True
                return

            # Try to load credentials from JSON string
            if settings.firebase_credentials_json:
                cred_dict = json.loads(settings.firebase_credentials_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized from JSON string")
                self._initialized = True
                return

            logger.warning("Firebase credentials not provided - some features may not work")
            self._initialized = False

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self._initialized = False

    def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """
        Verify a Firebase ID token

        Args:
            id_token: Firebase ID token from the client

        Returns:
            Decoded token payload if valid, None if invalid

        Raises:
            ValueError: If Firebase is not initialized
        """
        if not self._initialized:
            raise ValueError("Firebase is not initialized")

        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            return None
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token")
            return None
        except Exception as e:
            logger.error(f"Error verifying Firebase token: {e}")
            return None

    def get_user(self, uid: str) -> Optional[Dict]:
        """
        Get user information from Firebase

        Args:
            uid: Firebase UID

        Returns:
            User information dict if found, None otherwise
        """
        if not self._initialized:
            raise ValueError("Firebase is not initialized")

        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "email_verified": user.email_verified
            }
        except Exception as e:
            logger.error(f"Error getting Firebase user: {e}")
            return None


# Global instance
firebase_service = FirebaseService()
