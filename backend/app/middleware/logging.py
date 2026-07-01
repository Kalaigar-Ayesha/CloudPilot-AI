import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

logger = logging.getLogger("app.middleware.logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting unique correlation IDs, logging request durations,
    and capturing client agent metadata.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate correlation request ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Attach request ID to context
        request.state.correlation_id = correlation_id
        
        start_time = time.perf_counter()
        
        # Log request receipt
        logger.info(
            f"Incoming Request: {request.method} {request.url.path}",
            extra={
                "extra": {
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else "unknown",
                }
            }
        )
        
        try:
            response: Response = await call_next(request)
        except Exception as e:
            # Exceptions are formatted by the exception middleware immediately following
            logger.error(
                f"Request Exception generated: {str(e)}",
                extra={"extra": {"correlation_id": correlation_id}},
                exc_info=True
            )
            raise e
            
        process_time = time.perf_counter() - start_time
        
        # Add correlation ID to outgoing headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        
        logger.info(
            f"Outgoing Response: {request.method} {request.url.path} - Status: {response.status_code} - Timing: {process_time:.4f}s",
            extra={
                "extra": {
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "timing": process_time,
                }
            }
        )
        
        return response
