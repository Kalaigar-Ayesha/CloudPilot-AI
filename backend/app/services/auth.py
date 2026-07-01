from datetime import datetime, timedelta, timezone
import hashlib
import uuid
import jwt
import bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.base import AuthenticationException
from app.models.user import RefreshToken, User


class AuthService:
    """
    Implements JWT generation, password verification, and refresh token rotation.
    """
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against the stored bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def create_access_token(user_id: uuid.UUID, role: str) -> str:
        """
        Generates signed JWT Access Token containing subject and roles.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "type": "access"
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    async def create_refresh_token(db: AsyncSession, user_id: uuid.UUID) -> str:
        """
        Creates a new RefreshToken db entry and returns the raw token string.
        """
        raw_token = str(uuid.uuid4())
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_token)
        await db.flush()
        return raw_token

    @staticmethod
    async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[str, str, User]:
        """
        Verifies refresh token, invalidates it, generates a new one,
        and returns (new_access_token, new_refresh_token, user).
        """
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        
        # Query active token and user
        query = (
            select(RefreshToken, User)
            .join(User, User.id == RefreshToken.user_id)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
                User.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        record = result.first()

        if not record:
            raise AuthenticationException("Refresh token is invalid or has been revoked.")

        db_token, user = record

        # Check expiration
        if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            db_token.is_revoked = True
            await db.flush()
            raise AuthenticationException("Refresh token has expired. Please log in again.")

        # Invalidate old token (Rotation)
        db_token.is_revoked = True

        # Generate new credentials
        new_access = AuthService.create_access_token(user.id, user.role)
        new_refresh = await AuthService.create_refresh_token(db, user.id)
        
        await db.flush()
        return new_access, new_refresh, user

    @staticmethod
    async def revoke_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> None:
        """Revokes all refresh tokens for a user (force logout everywhere)."""
        query = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
        )
        await db.execute(query)
        await db.flush()
