from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
import re


class UserBase(BaseModel):
    """Base user fields shared across schemas"""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(
        ..., 
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Ensure password has minimum complexity.
        In production, you might want stricter rules.
        """
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "email": "john@example.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe"
            }]
        }
    )


class UserUpdate(BaseModel):
    """Schema for partial user updates (PATCH)"""
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "first_name": "Jane",
                "email": "newemail@example.com"
            }]
        }
    )


class UserResponse(UserBase):
    """Public user data returned by API (no sensitive info)"""
    id: int
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "id": 1,
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "is_verified": True,
                "created_at": "2025-10-22T10:00:00Z",
                "updated_at": None
            }]
        }
    )


class UserListResponse(BaseModel):
    """Response for listing multiple users (admin endpoint)"""
    users: list[UserResponse]
    total: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "users": [{
                    "id": 1,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "user",
                    "is_verified": True,
                    "created_at": "2025-10-22T10:00:00Z",
                    "updated_at": None
                }],
                "total": 1
            }]
        }
    )


class UserInDB(UserResponse):
    """
    Internal schema with sensitive data.
    Never return this directly to clients.
    """
    hashed_password: str
    verification_code: Optional[str] = None
