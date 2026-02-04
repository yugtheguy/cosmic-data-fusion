"""
Pydantic schemas for authentication and user management.

These schemas define the request/response models for authentication
endpoints and user data validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Token schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token payload."""
    email: Optional[str] = None


# User schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserUpdatePassword(BaseModel):
    """Schema for updating user password."""
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserInDB(UserBase):
    """User schema as stored in database."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """User schema for API responses (public safe)."""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserResponseWithToken(UserResponse):
    """User response with JWT token (for login/register)."""
    access_token: str
    token_type: str = "bearer"
