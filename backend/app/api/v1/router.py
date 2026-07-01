from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.cloud import router as cloud_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.billing import router as billing_router
from app.api.v1.optimization import router as optimization_router
from app.api.v1.ai import router as ai_router

api_v1_router = APIRouter()

# Register sub-routers
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(health_router, prefix="/health", tags=["Health & Status"])
api_v1_router.include_router(cloud_router, prefix="/cloud", tags=["Cloud Accounts"])
api_v1_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring & Metrics"])
api_v1_router.include_router(billing_router, prefix="/billing", tags=["Billing & Pricing"])
api_v1_router.include_router(optimization_router, prefix="/optimization", tags=["Optimization Engine"])
api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI DevOps Copilot"])
