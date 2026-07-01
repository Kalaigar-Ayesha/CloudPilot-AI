import logging
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.config import settings
from app.domains.billing.adapters.factory import BillingProviderFactory, PricingProviderFactory
from app.exceptions.base import ValidationException, ProviderException
from app.models.billing import BillingRecord, PricingRecord, ForecastReport
from app.repositories.billing import (
    billing_record_repository,
    pricing_record_repository,
    forecast_report_repository,
)
from app.repositories.cloud import cloud_account_repository, resource_repository
from app.utils.security import decrypt_payload

logger = logging.getLogger("app.services.billing")


class BillingService:
    """
    Coordinates multi-cloud billing aggregations, retail price catalog fetches,
    regression forecasting, and Redis caching.
    """

    @staticmethod
    async def sync_billing(
        db: AsyncSession,
        account_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Polls billing data from adapter, maps and saves records to DB."""
        account = await cloud_account_repository.get_with_credentials(db, account_id)
        if not account or not account.credentials:
            raise ValidationException(f"Cloud account {account_id} not found or credentials missing.")

        # 1. Recover credentials
        plaintext = decrypt_payload(account.credentials.encrypted_payload)
        creds = json.loads(plaintext)

        # 2. Resolve adapter
        adapter_class = BillingProviderFactory.get_adapter(account.provider_id)
        adapter = adapter_class()
        
        adapter.connect(creds)
        dtos = adapter.fetch_historical_cost(start_time, end_time)
        adapter.disconnect()

        # 3. Save billing records in DB
        sync_count = 0
        for dto in dtos:
            # Check for resource correlation matching external_id
            res_id = None
            if dto.resource_id:
                res = await resource_repository.get_by_external_id(
                    db,
                    cloud_account_id=account_id,
                    external_id=dto.resource_id
                )
                if res:
                    res_id = res.id

            billing_data = {
                "cloud_account_id": account_id,
                "resource_id": res_id,
                "usage_start": dto.usage_start,
                "usage_end": dto.usage_end,
                "cost": dto.cost,
                "currency": dto.currency,
                "usage_type": dto.usage_type,
                "category": dto.category,
                "raw_billing_payload": dto.raw_payload
            }

            await billing_record_repository.create(db, obj_in=billing_data)
            sync_count += 1

        # 4. Invalidate cache
        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                cache_key = f"cloudpilot:proj:{account.project_id}:billing:*"
                keys = await r.keys(cache_key)
                if keys:
                    await r.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to evict billing cache: {str(e)}")

        logger.info(f"Synchronized {sync_count} billing logs for account {account_id}")
        return sync_count

    @staticmethod
    async def refresh_pricing(db: AsyncSession, provider_id: str, region: str) -> int:
        """Polls regional catalog rate cards and updates pricing database tables."""
        # Resolve pricing provider
        adapter_class = PricingProviderFactory.get_adapter(provider_id)
        adapter = adapter_class()
        
        # Public catalogs typically do not require authentication
        adapter.connect({})
        dtos = adapter.fetch_compute_pricing(region)

        sync_count = 0
        for dto in dtos:
            # Query existing SKU rate
            existing = await pricing_record_repository.lookup_sku(
                db,
                provider_id=provider_id,
                sku=dto.sku,
                region=region
            )

            pricing_data = {
                "provider_id": provider_id,
                "sku": dto.sku,
                "service_code": dto.service_code,
                "region": dto.region,
                "resource_specification": dto.resource_specification,
                "unit_price_hourly": dto.unit_price_hourly,
                "currency": dto.currency
            }

            if existing:
                await pricing_record_repository.update(db, db_obj=existing, obj_in=pricing_data)
            else:
                await pricing_record_repository.create(db, obj_in=pricing_data)
            
            sync_count += 1

        logger.info(f"Refreshed {sync_count} pricing rate cards for provider {provider_id} in region {region}")
        return sync_count

    @staticmethod
    async def get_dashboard_summary(db: AsyncSession, project_id: uuid.UUID) -> dict:
        """Aggregates multicloud billing dashboard (Redis cache-aside pattern)."""
        cache_key = f"cloudpilot:proj:{project_id}:billing:dashboard"
        
        try:
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
            async with r:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache query failed: {str(e)}")

        accounts = await cloud_account_repository.get_by_project(db, project_id)
        account_ids = [acc.id for acc in accounts]

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=30)

        # Get database summary
        summary = await billing_record_repository.get_summary(db, account_ids, start_time, end_time)

        # Aggregate spend by provider
        by_provider = {}
        for acc in accounts:
            cost = summary["by_account"].get(str(acc.id), 0.0)
            by_provider[acc.provider_id] = by_provider.get(acc.provider_id, 0.0) + cost

        response_data = {
            "total_cost": summary["total"],
            "currency": "USD",
            "by_provider": by_provider,
            "by_category": summary["by_category"]
        }

        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                await r.set(cache_key, json.dumps(response_data), ex=600)  # 10 minutes cache
        except Exception as e:
            logger.warning(f"Failed to cache billing dashboard summary: {str(e)}")

        return response_data

    @staticmethod
    async def generate_forecast(db: AsyncSession, project_id: uuid.UUID) -> ForecastReport:
        """
        Computes 30-day billing projections utilizing Linear Regression models.
        """
        accounts = await cloud_account_repository.get_by_project(db, project_id)
        account_ids = [acc.id for acc in accounts]

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=30)

        # Get daily trends for last 30 days
        trends = await billing_record_repository.get_trends(db, account_ids, start_time, end_time, "daily")
        
        # Calculate linear regression: y = mx + c
        n = len(trends)
        if n < 2:
            # Fallback if insufficient historical logs exist
            forecast_points = [
                {"month": "Month +1", "baseline": 100.0, "optimistic": 90.0, "pessimistic": 115.0}
            ]
            baseline_cost = 100.0
            optimistic_cost = 90.0
            pessimistic_cost = 115.0
        else:
            x_vals = list(range(1, n + 1))
            y_vals = [t["cost"] for t in trends]
            
            sum_x = sum(x_vals)
            sum_y = sum(y_vals)
            sum_x_sq = sum(x**2 for x in x_vals)
            sum_xy = sum(x*y for x, y in zip(x_vals, y_vals))
            
            denominator = (n * sum_x_sq) - (sum_x ** 2)
            if denominator == 0:
                m = 0.0
            else:
                m = ((n * sum_xy) - (sum_x * sum_y)) / denominator
            c = (sum_y - (m * sum_x)) / n

            # Forecast next 30 days
            forecast_points = []
            baseline_cost = 0.0
            
            for i in range(1, 31):
                pred_day = n + i
                pred_val = max(0.0, (m * pred_day) + c)
                baseline_cost += pred_val
                
                # Dynamic prediction buckets
                forecast_points.append({
                    "day": i,
                    "baseline": round(pred_val, 2),
                    "optimistic": round(pred_val * 0.9, 2),
                    "pessimistic": round(pred_val * 1.15, 2)
                })
            
            optimistic_cost = baseline_cost * 0.9
            pessimistic_cost = baseline_cost * 1.15

        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        forecast_data = {
            "project_id": project_id,
            "forecast_type": "cost",
            "baseline_cost": round(baseline_cost, 2),
            "optimistic_cost": round(optimistic_cost, 2),
            "pessimistic_cost": round(pessimistic_cost, 2),
            "forecast_data": {"points": forecast_points},
            "start_date": start_date,
            "end_date": end_date
        }

        db_forecast = await forecast_report_repository.create(db, obj_in=forecast_data)
        await db.flush()
        return db_forecast
