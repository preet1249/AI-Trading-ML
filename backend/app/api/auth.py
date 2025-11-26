"""
Authentication API Routes
- Sign up, login, logout
- Token refresh
- Password reset
- JWT token validation
"""
from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@router.post("/signup", response_model=APIResponse)
async def signup(request: SignupRequest):
    """
    Create new user account

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: Optional full name

    Returns:
        - User data with access token
        - Email verification sent
    """
    success, message, data = await auth_service.signup(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return APIResponse(
        success=True,
        message=message,
        data=data
    )


@router.post("/login", response_model=APIResponse)
async def login(request: LoginRequest):
    """
    Login with email and password

    - **email**: User email
    - **password**: User password

    Returns:
        - Access token (30min expiry)
        - Refresh token (7 day expiry)
        - User data
    """
    success, message, data = await auth_service.login(
        email=request.email,
        password=request.password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    return APIResponse(
        success=True,
        message=message,
        data=data
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token

    Returns:
        - New access token
        - New refresh token
    """
    success, message, data = await auth_service.refresh_token(
        refresh_token=request.refresh_token
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    return APIResponse(
        success=True,
        message=message,
        data=data
    )


@router.post("/logout", response_model=APIResponse)
async def logout(authorization: Optional[str] = Header(None)):
    """
    Logout user (invalidate token)

    Requires:
        - Authorization header with Bearer token
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    success, message = await auth_service.logout(token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return APIResponse(
        success=True,
        message=message
    )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Send password reset email

    - **email**: User email

    Returns:
        - Success message (doesn't reveal if email exists)
    """
    success, message = await auth_service.reset_password(
        email=request.email
    )

    # Always return success (don't reveal if email exists)
    return APIResponse(
        success=True,
        message="If that email exists, a reset link has been sent"
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current user profile

    Requires:
        - Authorization header with Bearer token

    Returns:
        - User profile data
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    user_data = await auth_service.verify_token(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return APIResponse(
        success=True,
        message="User authenticated",
        data=user_data
    )


@router.get("/verify-token")
async def verify_token(authorization: Optional[str] = Header(None)):
    """
    Verify if JWT token is valid

    Requires:
        - Authorization header with Bearer token

    Returns:
        - Token validity status
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    user_data = await auth_service.verify_token(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "valid": True,
        "user_id": user_data.get("id"),
        "email": user_data.get("email")
    }
