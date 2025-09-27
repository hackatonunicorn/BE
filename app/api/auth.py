from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
import uuid
import secrets

from app.core.database import get_db
from app.core.auth import auth_manager, get_current_active_user
from app.data.models import User, UserRole
from app.api.auth_schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    RefreshTokenRequest, PasswordResetRequest, PasswordReset,
    EmailVerificationRequest, ChangePasswordRequest, AuthResponse
)
from app.core.config_simple import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    username = user_data.email.split('@')[0]
    counter = 1
    original_username = username
    while db.query(User).filter(User.username == username).first():
        username = f"{original_username}{counter}"
        counter += 1
    
    # Create new user
    hashed_password = auth_manager.get_password_hash(user_data.password)
    
    new_user = User(
        username=username,
        email=user_data.email,
        full_name=user_data.full_name,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        company_name=user_data.company_name,
        role=user_data.role,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,  # Email verification required
        is_superuser=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    access_token = auth_manager.create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email, "role": new_user.role.value}
    )
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    
    # TODO: Send email verification
    # await send_verification_email(new_user.email, verification_token)
    
    return AuthResponse(
        user=UserResponse.from_orm(new_user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )

@router.post("/login", response_model=AuthResponse)
async def login_user(user_credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    
    user = auth_manager.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if user_credentials.remember_me:
        access_token_expires = timedelta(days=30)
    
    access_token = auth_manager.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds())
        )
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    
    try:
        payload = auth_manager.verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = auth_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Keep the same refresh token
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should discard tokens)"""
    # In a stateless JWT system, logout is handled on the client side
    # You could implement token blacklisting here if needed
    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not auth_manager.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = auth_manager.get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/forgot-password")
async def forgot_password(password_reset: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send password reset email"""
    
    user = db.query(User).filter(User.email == password_reset.email).first()
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # TODO: Store reset token in database with expiration
    # TODO: Send reset email
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(password_reset: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using reset token"""
    
    # TODO: Verify reset token from database
    # TODO: Check token expiration
    
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet"
    )

@router.post("/verify-email")
async def verify_email(verification: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Verify user email address"""
    
    # TODO: Verify token from database
    # TODO: Mark user as verified
    
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email verification not implemented yet"
    )

@router.post("/resend-verification")
async def resend_verification_email(current_user: User = Depends(get_current_active_user)):
    """Resend email verification"""
    
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # TODO: Send verification email
    
    return {"message": "Verification email sent"}

@router.delete("/account")
async def delete_account(
    password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    
    # Verify password
    if not auth_manager.verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Deactivate user instead of deleting for data integrity
    current_user.is_active = False
    db.commit()
    
    return {"message": "Account deactivated successfully"}
