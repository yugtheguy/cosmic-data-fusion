"""
Authentication API endpoints.

Provides user registration, login, and profile management endpoints
with JWT token-based authentication.
"""

from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.email_utils import send_welcome_email, send_verification_email
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_superuser,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_verification_token,
    decode_access_token
)
from app.auth_schemas import (
    UserCreate,
    UserResponse,
    UserResponseWithToken,
    UserUpdate,
    UserUpdatePassword,
    Token,
    UserInDB
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponseWithToken, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with hashed password and returns a JWT token
    for immediate authentication.
    
    Args:
        user_data: User registration data (email, password, full_name)
        db: Database session
        
    Returns:
        User profile with JWT access token
        
    Raises:
        HTTPException: If email already registered
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    
    if existing_user and existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Prepare password hash
    hashed_password = get_password_hash(user_data.password)
    
    if existing_user:
        # Update existing unverified user
        existing_user.hashed_password = hashed_password
        existing_user.full_name = user_data.full_name
        new_user = existing_user
    else:
        # Create new user
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=False, # Wait for email verification
            is_superuser=False
        )
        db.add(new_user)
    
    db.commit()
    db.refresh(new_user)
    
    # Generate verification token
    verification_token = create_verification_token(new_user.email)

    # Send verification email
    background_tasks.add_task(send_verification_email, new_user.email, verification_token)
    
    # Return basic info without access token
    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at,
        "access_token": "", # No token until verified
        "token_type": "bearer"
    }


@router.get("/verify-email")
async def verify_email(token: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Verify email address using the token.
    
    Activates the user account and sends a welcome email.
    """
    email = decode_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if user.is_active:
        return {"message": "Email already verified"}
        
    # Activate user
    user.is_active = True
    db.commit()
    
    # Send welcome email
    background_tasks.add_task(send_welcome_email, user.email, user.full_name)
    
    return {"message": "Email verified successfully! You can now login."}


@router.post("/login", response_model=UserResponseWithToken)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Authenticates user credentials and returns a JWT token.
    Uses OAuth2PasswordRequestForm for compatibility with OAuth2 flow.
    
    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        User profile with JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        User profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    Args:
        user_update: Fields to update (full_name, email)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If email already taken by another user
    """
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    # Update full_name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/me/password")
async def update_password(
    password_update: UserUpdatePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's password.
    
    Args:
        password_update: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    from app.auth import verify_password
    
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/users", response_model=List[UserInDB])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        admin: Current superuser (admin)
        db: Database session
        
    Returns:
        List of user profiles
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete a user account (admin only).
    
    Soft delete by setting is_active to False.
    
    Args:
        user_id: ID of user to delete
        admin: Current superuser (admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.email} deactivated successfully"}
