import logging
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.base import BaseAppException

logger = logging.getLogger("app.middleware.exceptions")


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware catching all application exceptions and mapping them
    to standard Unified Response formats.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return self._handle_exception(request, exc)

    def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        status_code = 500
        message = "An unexpected error occurred on the server."
        errors = []
        metadata = {"correlation_id": correlation_id}

        # 1. Custom Application Exceptions
        if isinstance(exc, BaseAppException):
            status_code = exc.status_code
            message = exc.message
            errors = exc.errors
            metadata.update(exc.metadata)
            logger.warning(f"Application error [{status_code}]: {message}")

        # 2. Pydantic / FastAPI Input Validation Exceptions
        elif isinstance(exc, RequestValidationError):
            status_code = 400
            message = "Validation rules check failed."
            for err in exc.errors():
                # Extract field path
                field = " -> ".join(str(loc) for loc in err.get("loc", []))
                errors.append({
                    "field": field,
                    "type": err.get("type"),
                    "detail": err.get("msg")
                })
            logger.warning(f"Request validation failure: {errors}")

        # 3. Database Errors
        elif isinstance(exc, SQLAlchemyError):
            status_code = 500
            message = "A database transaction error occurred."
            logger.error("SQLAlchemy exception generated.", exc_info=True)

        # 4. Fallback Raw Errors
        else:
            logger.error(f"Unhandled Python error: {str(exc)}", exc_info=True)

        # Unified response dictionary structure
        response_body = {
            "status": "error",
            "message": message,
            "data": None,
            "metadata": metadata,
            "errors": errors,
            "timestamp": timestamp
        }

        return JSONResponse(
            status_code=status_code,
            content=response_body
        )
