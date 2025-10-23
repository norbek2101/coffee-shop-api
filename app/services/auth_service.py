import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from app.core.config import settings

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, request: SignupRequest) -> TokenResponse:
    """
    Register new user and generate verification code.
    Returns JWT tokens for immediate authentication.
    """
    # Check email uniqueness
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate 6-digit verification code
    verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.VERIFICATION_CODE_EXPIRE_HOURS
    )
    
    # Create user with hashed verification code for security
    new_user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole.USER,
        is_verified=False,
        verification_code=hash_password(verification_code),  # Hash it for security
        verification_code_expires_at=expires_at
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # In production, send this via email/SMS
    # For now, just log it
    logger.info(f"Verification code for {new_user.email}: {verification_code}")
    print(f"\n{'='*60}")
    print(f"VERIFICATION CODE FOR {new_user.email}")
    print(f"Code: {verification_code}")
    print(f"Expires at: {expires_at.isoformat()}")
    print(f"{'='*60}\n")
    
    # Generate JWT tokens
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


async def login_user(db: AsyncSession, request: LoginRequest) -> TokenResponse:
    """
    Authenticate user with email/password.
    Returns JWT token pair on success.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    # Validate credentials
    if not user or not verify_password(request.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User logged in: {user.email}")
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

async def verify_email(db: AsyncSession, code: str, user: User) -> dict:
    """Verify user's email using the 6-digit code."""
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    if not user.verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found. Please request a new one."
        )
    
    # Handle timezone-naive datetimes (SQLite issue)
    if user.verification_code_expires_at:
        expires_at = user.verification_code_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired. Please request a new one."
            )
    
    if not verify_password(code, user.verification_code):
        logger.warning(f"Invalid verification code attempt for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    
    await db.commit()
    
    logger.info(f"Email verified for user: {user.email}")
    
    return {
        "message": "Email verified successfully",
        "email": user.email
    }


async def resend_verification_code(db: AsyncSession, user: User) -> dict:
    """
    Generate and send a new verification code.
    Useful when the original code expires.
    """
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new code
    verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.VERIFICATION_CODE_EXPIRE_HOURS
    )
    
    # Update user
    user.verification_code = hash_password(verification_code)
    user.verification_code_expires_at = expires_at
    
    await db.commit()
    
    # In production, send via email/SMS
    logger.info(f"New verification code for {user.email}: {verification_code}")
    print(f"\n{'='*60}")
    print(f"NEW VERIFICATION CODE FOR {user.email}")
    print(f"Code: {verification_code}")
    print(f"Expires at: {expires_at.isoformat()}")
    print(f"{'='*60}\n")
    
    return {
        "message": "New verification code sent",
        "expires_at": expires_at.isoformat()
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """
    Generate new access token using valid refresh token.
    Also issues a new refresh token for security (token rotation).
    """
    try:
        payload = decode_token(refresh_token)
        
        # Verify it's actually a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        try:
            user_id = int(user_id_str)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate new token pair (token rotation for better security)
    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    logger.info(f"Token refreshed for user: {user.email}")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,  # Return new refresh token
        token_type="bearer"
    )


async def update_user_role(db: AsyncSession, user_id: int, new_role: UserRole) -> User:
    """
    Update user role (e.g., promote to admin).
    Admin-only operation.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    old_role = user.role
    user.role = new_role
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User {user.email} role changed from {old_role} to {new_role}")
    
    return user
