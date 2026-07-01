import logging
from fastapi import APIRouter, Depends, Response, Request
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.exceptions.base import AuthenticationException, ValidationException
from app.models.user import User
from app.repositories.user import user_repository
from app.schemas.base import UnifiedResponse
from app.schemas.user import (
    UserLogin,
    UserOut,
    UserRegister,
    TokenOut,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.services.auth import AuthService

logger = logging.getLogger("app.api.v1.auth")
router = APIRouter()


@router.post("/register", response_model=UnifiedResponse[UserOut], status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    """Registers a new user. The first user registration defaults to 'admin' role."""
    # Check if user already exists
    existing_user = await user_repository.get_by_email(db, payload.email)
    if existing_user:
        raise ValidationException("A user with this email address already exists.")

    # Determine role (first user is admin)
    user_count = await user_repository.count(db)
    role = "admin" if user_count == 0 else "viewer"

    hashed_password = AuthService.hash_password(payload.password)
    user_data = {
        "email": payload.email.lower(),
        "password_hash": hashed_password,
        "role": role,
        "is_active": True
    }
    
    new_user = await user_repository.create(db, obj_in=user_data)
    await db.commit()
    
    logger.info(f"Registered user: {payload.email} with role: {role}")
    return {
        "status": "success",
        "message": "User registered successfully.",
        "data": new_user,
        "metadata": {},
        "errors": []
    }


@router.post("/login", response_model=UnifiedResponse[TokenOut])
async def login(
    payload: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Logs in user, issuing access token and setting secure refresh cookie."""
    user = await user_repository.get_by_email(db, payload.email)
    if not user or not AuthService.verify_password(payload.password, user.password_hash):
        raise AuthenticationException("Invalid email credentials or password.")

    if not user.is_active:
        raise AuthenticationException("User account has been deactivated.")

    # Create tokens
    access_token = AuthService.create_access_token(user.id, user.role)
    refresh_token = await AuthService.create_refresh_token(db, user.id)
    await db.commit()

    # Set HTTP-Only Cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",  # Set to secure for https in prod
        samesite="strict",
        path="/api/v1/auth",  # Scopes cookie access to refresh/logout paths
        max_age=7 * 24 * 3600  # 7 days
    )

    logger.info(f"User login successful: {user.email}")
    return {
        "status": "success",
        "message": "Authentication successful.",
        "data": TokenOut(access_token=access_token, token_type="Bearer", expires_in=900),
        "metadata": {},
        "errors": []
    }


@router.post("/refresh", response_model=UnifiedResponse[TokenOut])
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Rotates refresh token and generates new access token using secure cookie."""
    raw_refresh_token = request.cookies.get("refresh_token")
    if not raw_refresh_token:
        raise AuthenticationException("Session refresh token cookie missing.")

    # Rotate refresh token
    new_access, new_refresh, user = await AuthService.rotate_refresh_token(db, raw_refresh_token)
    await db.commit()

    # Set new secure cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600
    )

    return {
        "status": "success",
        "message": "Access token refreshed successfully.",
        "data": TokenOut(access_token=new_access, token_type="Bearer", expires_in=900),
        "metadata": {},
        "errors": []
    }


@router.post("/logout", response_model=UnifiedResponse[None])
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logs out user, revoking all active sessions for security."""
    await AuthService.revoke_user_sessions(db, current_user.id)
    await db.commit()

    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth"
    )

    logger.info(f"User logout: {current_user.email}")
    return {
        "status": "success",
        "message": "Logged out successfully. All sessions revoked.",
        "data": None,
        "metadata": {},
        "errors": []
    }


@router.post("/forgot-password", response_model=UnifiedResponse[None])
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Triggers forgot password email flow (Mock structure)."""
    user = await user_repository.get_by_email(db, payload.email)
    if user:
        logger.info(f"Forgot password reset link requested for: {payload.email}")
        # In a real environment, generate token and dispatch email queue task
    
    return {
        "status": "success",
        "message": "If the email is registered, a password reset link has been dispatched.",
        "data": None,
        "metadata": {},
        "errors": []
    }


@router.post("/reset-password", response_model=UnifiedResponse[None])
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Resets user password using valid token (Mock structure)."""
    # Simulate token resolution to user ID
    if payload.token == "expired_token":
        raise ValidationException("Password reset token is invalid or has expired.")

    # Mock user update
    logger.info("Password updated successfully via password-reset verification.")
    return {
        "status": "success",
        "message": "Password has been reset successfully. Please log in with your new password.",
        "data": None,
        "metadata": {},
        "errors": []
    }
