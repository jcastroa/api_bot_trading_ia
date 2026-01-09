"""
JWT service for token generation and validation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt

from app.config import settings


class JWTService:
    """Service for JWT token operations"""

    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_days = settings.jwt_expiration_days

    def create_access_token(
        self,
        user_id: int,
        firebase_uid: str,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new JWT access token

        Args:
            user_id: Database user ID
            firebase_uid: Firebase UID
            email: User email
            expires_delta: Optional custom expiration time

        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.expiration_days)

        payload = {
            "user_id": user_id,
            "firebase_uid": firebase_uid,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def decode_token(self, token: str) -> Dict:
        """
        Decode a JWT token without verification (use with caution)

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            JWTError: If token is malformed
        """
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


# Global instance
jwt_service = JWTService()
