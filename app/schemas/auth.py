from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8,
        description="Password must be at least 8 characters"
    )
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe"
            }]
        }
    }


class LoginRequest(BaseModel):
    """User login credentials"""
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "password": "SecurePass123"
            }]
        }
    }


class TokenResponse(BaseModel):
    """JWT token pair returns after login or refresh"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }
    }


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str = Field(..., description="Valid refresh token")


class VerifyEmailRequest(BaseModel):
    """Email verification with code"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "code": "123456"
            }]
        }
    }


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "message": "Operation completed successfully"
            }]
        }
    }
