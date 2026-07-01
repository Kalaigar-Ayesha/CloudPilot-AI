import re
import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+=\-\[\]{}|;:',.<>?/]).{12,128}$"
)


class UserRegister(BaseModel):
    """Schema validating user registration requests."""
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must be between 12-128 characters, containing at least "
                "one uppercase letter, one lowercase letter, one number, and one special character."
            )
        return v


class UserLogin(BaseModel):
    """Schema validating login credentials."""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Safe database model representation output."""
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    """Access token delivery schema."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # seconds


class ForgotPasswordRequest(BaseModel):
    """Forgot password trigger payload."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password completion payload."""
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError("Password complexity rules not met.")
        return v
