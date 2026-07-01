from typing import Any, Dict, List, Optional


class BaseAppException(Exception):
    """Base exception class for all custom application errors."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        errors: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        self.metadata = metadata or {}


class ValidationException(BaseAppException):
    """Raised when request payload verification fails."""
    def __init__(self, message: str = "Validation failed.", errors: Optional[List[Any]] = None):
        super().__init__(message=message, status_code=400, errors=errors)


class AuthenticationException(BaseAppException):
    """Raised when authentication credentials fail or expire."""
    def __init__(self, message: str = "Authentication credentials invalid or missing."):
        super().__init__(message=message, status_code=401)


class AuthorizationException(BaseAppException):
    """Raised when RBAC checks confirm insufficient rights."""
    def __init__(self, message: str = "Insufficient permission scopes for target request."):
        super().__init__(message=message, status_code=403)


class DatabaseException(BaseAppException):
    """Raised when database interactions fail."""
    def __init__(self, message: str = "Database transaction operation failed.", errors: Optional[List[Any]] = None):
        super().__init__(message=message, status_code=500, errors=errors)


class ProviderException(BaseAppException):
    """Raised when external integrations (cloud/monitoring) return errors."""
    def __init__(self, message: str, status_code: int = 502, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status_code, metadata=metadata)
