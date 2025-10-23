from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import (
    SignupRequest, 
    LoginRequest, 
    TokenResponse, 
    VerifyEmailRequest,
    RefreshTokenRequest,
    MessageResponse
)
from app.services import auth_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. Email must be unique. Returns JWT tokens"
)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register new user and return JWT tokens"""
    return await auth_service.register_user(db, request)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password. Returns access token (30min) and refresh token (7 days)."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    return await auth_service.login_user(db, request)


@router.post(
    "/verify",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify email using 6-digit code. Requires authentication. Code expires in 24 hours."
)
async def verify_email(
    request: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify user's email with verification code"""
    return await auth_service.verify_email(db, request.code, current_user)


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification code",
    description="Request a new verification code if the original expired. Requires authentication."
)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate and send new verification code"""
    return await auth_service.resend_verification_code(db, current_user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access and refresh tokens using valid refresh token. Implements token rotation for security."
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Issue new token pair using refresh token"""
    return await auth_service.refresh_access_token(db, request.refresh_token)
