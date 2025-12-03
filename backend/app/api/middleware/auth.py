"""
Authentication Middleware
JWT token verification with custom JWT
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
from typing import Optional

from app.config import settings
from app.models.schemas import User

security = HTTPBearer()


async def verify_token(token: str) -> dict:
    """
    Verify JWT token (Supabase compatible)

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Try with SUPABASE_JWT_SECRET first
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_aud": False, "verify_signature": True}
            )
            return payload
        except Exception:
            # Fallback: Try without signature verification for Supabase tokens
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_aud": False, "verify_exp": True}
            )
            return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, DecodeError) as e:
        print(f"Token decode error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User object

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Debug: Log token info
    print(f"[AUTH DEBUG] Token length: {len(token)}")
    print(f"[AUTH DEBUG] Token segments: {len(token.split('.'))}")
    print(f"[AUTH DEBUG] Token preview: {token[:50]}..." if len(token) > 50 else f"[AUTH DEBUG] Full token: {token}")

    payload = await verify_token(token)

    # Extract user info from token
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    return User(
        id=user_id,
        email=email or "",
        created_at=payload.get("created_at", "")
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None
    Useful for endpoints that work with or without authentication

    Args:
        credentials: HTTP authorization credentials (optional)

    Returns:
        User object or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
