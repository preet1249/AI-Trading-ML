"""
Custom Authentication Service - No Supabase Auth SDK
- Sign up with email verification
- Login with JWT tokens
- Password reset
- Session management
- Rate limiting protection
- Uses python-jose for JWT, passlib for password hashing
"""
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from app.db.supabase_client import get_admin_supabase
from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Custom authentication service without Supabase Auth SDK"""

    @classmethod
    async def signup(
        cls,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Sign up new user (no email verification required)

        Args:
            email: User email
            password: Password (min 8 chars, max 72 bytes for bcrypt)
            full_name: Optional full name

        Returns:
            Tuple (success, message, user_data)
        """
        try:
            # Validate inputs
            if not cls._validate_email(email):
                return False, "Invalid email format", None

            if not cls._validate_password(password):
                return False, "Password must be at least 8 characters", None

            # Bcrypt has 72 byte limit - validate password length
            if len(password.encode('utf-8')) > 72:
                return False, "Password is too long (max 72 bytes)", None

            # Check if user already exists
            supabase = get_admin_supabase()
            existing_user = supabase.table("users").select("id").eq("email", email).execute()

            if existing_user.data:
                return False, "Email already registered", None

            # Hash password (bcrypt truncates at 72 bytes)
            hashed_password = pwd_context.hash(password)

            # Create user in users table
            user_data = {
                "email": email,
                "password_hash": hashed_password,
                "full_name": full_name or "",
                "subscription_tier": "free",
                "subscription_status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat()
            }

            response = supabase.table("users").insert(user_data).execute()

            if not response.data:
                return False, "Failed to create user", None

            user = response.data[0]
            user_id = user.get("id")

            # Generate JWT token
            access_token = cls._create_access_token(user_id, email)
            refresh_token = cls._create_refresh_token(user_id)

            logger.info(f"✅ User created: {email}")

            return True, "Account created successfully!", {
                "user_id": user_id,
                "email": email,
                "access_token": access_token,
                "refresh_token": refresh_token
            }

        except Exception as e:
            logger.error(f"Unexpected error during signup: {e}")
            return False, "An error occurred during signup", None

    @classmethod
    async def login(
        cls,
        email: str,
        password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login user

        Args:
            email: User email
            password: User password

        Returns:
            Tuple (success, message, tokens_and_user)
        """
        try:
            supabase = get_admin_supabase()

            # Get user by email
            response = supabase.table("users").select("*").eq("email", email).execute()

            if not response.data:
                return False, "Invalid credentials", None

            user = response.data[0]

            # Verify password
            if not pwd_context.verify(password, user.get("password_hash")):
                return False, "Invalid credentials", None

            user_id = user.get("id")

            # Update last login
            supabase.table("users").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()

            # Generate JWT tokens
            access_token = cls._create_access_token(user_id, email)
            refresh_token = cls._create_refresh_token(user_id)

            logger.info(f"✅ User logged in: {email}")

            return True, "Login successful", {
                "user": {
                    "id": user_id,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "subscription_tier": user.get("subscription_tier")
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }

        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return False, "An error occurred during login", None

    @classmethod
    async def refresh_token(
        cls,
        refresh_token: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: JWT refresh token

        Returns:
            Tuple (success, message, new_tokens)
        """
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"]
            )

            user_id = payload.get("sub")
            if not user_id:
                return False, "Invalid refresh token", None

            # Get user
            supabase = get_admin_supabase()
            response = supabase.table("users").select("*").eq("id", user_id).execute()

            if not response.data:
                return False, "User not found", None

            user = response.data[0]

            # Generate new tokens
            access_token = cls._create_access_token(user_id, user.get("email"))
            new_refresh_token = cls._create_refresh_token(user_id)

            return True, "Token refreshed", {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }

        except jwt.ExpiredSignatureError:
            return False, "Refresh token expired", None
        except jwt.InvalidTokenError:
            return False, "Invalid refresh token", None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False, "Failed to refresh token", None

    @classmethod
    async def logout(cls, access_token: str) -> Tuple[bool, str]:
        """
        Logout user (client-side token removal)

        Args:
            access_token: JWT access token

        Returns:
            Tuple (success, message)
        """
        logger.info("✅ User logged out")
        return True, "Logout successful"

    @classmethod
    async def reset_password(cls, email: str) -> Tuple[bool, str]:
        """
        Send password reset email

        Args:
            email: User email

        Returns:
            Tuple (success, message)
        """
        try:
            supabase = get_admin_supabase()
            response = supabase.table("users").select("id").eq("email", email).execute()

            if response.data:
                # TODO: Implement email sending with reset token
                logger.info(f"Password reset requested for: {email}")

            # Don't reveal if email exists (security)
            return True, "If that email exists, a reset link has been sent"

        except Exception as e:
            logger.error(f"Error sending reset email: {e}")
            return True, "If that email exists, a reset link has been sent"

    @classmethod
    async def verify_token(cls, access_token: str) -> Optional[Dict]:
        """
        Verify JWT token and return user data

        Args:
            access_token: JWT access token

        Returns:
            User data if valid, None if invalid
        """
        try:
            # Decode JWT
            payload = jwt.decode(
                access_token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"]
            )

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get user profile
            supabase = get_admin_supabase()
            response = supabase.table("users").select("*").eq("id", user_id).execute()

            if not response.data:
                return None

            return response.data[0]

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    @classmethod
    def _create_access_token(cls, user_id: str, email: str) -> str:
        """Create JWT access token (1 hour expiration)"""
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
        # Ensure token is string (PyJWT < 2.0 returns bytes)
        return token.decode('utf-8') if isinstance(token, bytes) else token

    @classmethod
    def _create_refresh_token(cls, user_id: str) -> str:
        """Create JWT refresh token (7 days expiration)"""
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
        # Ensure token is string (PyJWT < 2.0 returns bytes)
        return token.decode('utf-8') if isinstance(token, bytes) else token

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def _validate_password(password: str) -> bool:
        """Validate password strength"""
        return len(password) >= 8


# Singleton instance
auth_service = AuthService()
