import logging
import json
import uuid
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.config import settings
from app.domains.optimization.rules.base import RuleEvaluationContext
from app.domains.optimization.rules.registry import RuleRegistry
from app.exceptions.base import ValidationException
from app.models.optimization import Recommendation
from app.repositories.optimization import recommendation_repository
from app.repositories.cloud import resource_repository, cloud_account_repository
from app.repositories.monitoring import metric_repository
from app.repositories.billing import billing_record_repository

logger = logging.getLogger("app.services.optimization")


class OptimizationService:
    """
    Orchestrates scan executions, calculates confidence scores, prioritizes items,
    and updates Redis caches.
    """

    @staticmethod
    def calculate_confidence(context: RuleEvaluationContext) -> int:
        """
        Calculates a deterministic confidence score (0-100) based on metrics stability.
        """
        score = 80  # Base confidence
        metrics = context.metrics
        
        # 1. Monitoring Availability Check
        if len(metrics) < 5:
            score -= 20
        else:
            # 2. Metric Stability Check (standard deviation deviation)
            values = [m.get("value", 0.0) for m in metrics]
            std_dev = float(np.std(values)) if len(values) > 1 else 0.0
            if std_dev > 15.0:
                score -= 15  # Unstable metrics reduce confidence
                
        # 3. Resource Age Check
        created_at_str = context.resource.get("created_at")
        if created_at_str:
            try:
                # Handle ISO format
                created = datetime.fromisoformat(created_at_str)
                age_days = (datetime.now(timezone.utc) - created).days
                if age_days < 3:
                    score -= 10  # Low baseline history
            except Exception:
                pass

        return max(0, min(100, score))

    @staticmethod
    def calculate_priority(savings: float, risk_level: str, severity: str) -> str:
        """
        Deterministically prioritizes recommendations based on savings and risks.
        """
        if severity == "critical":
            return "high"
        if savings > 100.0 and risk_level == "low":
            return "high"
        if savings > 20.0 and risk_level in ("low", "medium"):
            return "medium"
        return "low"

    @staticmethod
    async def run_optimization_scan(db: AsyncSession, project_id: uuid.UUID) -> dict:
        """Queries inventory records and executes registered rules evaluation."""
        accounts = await cloud_account_repository.get_by_project(db, project_id)
        
        # Load all active resources
        resources = []
        for acc in accounts:
            acc_res = await resource_repository.get_by_account(db, acc.id)
            resources.extend(acc_res)

        # Clear existing ACTIVE recommendations to avoid duplicates
        existing = await recommendation_repository.get_by_project(db, project_id)
        for rec in existing:
            await recommendation_repository.remove(db, id=rec.id)
        await db.flush()

        rules = RuleRegistry.get_rules()
        recommendation_count = 0
        total_savings = 0.0

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)

        for res in resources:
            # 1. Fetch metrics
            db_metrics = await metric_repository.get_metrics(
                db, res.id, "cpu_utilization", start_time, end_time
            )
            metrics_payload = [
                {"metric_type": m.metric_type, "value": m.value, "timestamp": m.timestamp.isoformat()}
                for m in db_metrics
            ]

            # 2. Fetch billing history
            db_billing = await billing_record_repository.get_trends(
                db, [res.cloud_account_id], start_time, end_time, "daily"
            )

            # Build resource payload
            res_payload = {
                "id": str(res.id),
                "external_id": res.external_id,
                "name": res.name,
                "resource_type": res.resource_type,
                "region": res.region,
                "status": res.status,
                "created_at": res.created_at.isoformat() if res.created_at else None,
                "raw_payload": res.raw_payload
            }

            # Build evaluation context
            context = RuleEvaluationContext(
                resource=res_payload,
                metrics=metrics_payload,
                pricing={"unit_price_hourly": 0.045},  # Default pricing fallback
                historical_billing=list(db_billing)
            )

            # 3. Evaluate rules
            for rule in rules:
                # Match provider and resource type
                if res.resource_type not in rule.applicable_resource_types:
                    continue
                
                try:
                    result = rule.evaluate(context)
                    if result.is_applicable:
                        confidence = OptimizationService.calculate_confidence(context)
                        priority = OptimizationService.calculate_priority(
                            result.estimated_savings, result.risk_level, result.severity
                        )

                        rec_data = {
                            "project_id": project_id,
                            "resource_id": res.id,
                            "provider_id": res_payload["external_id"].split(":")[0] if ":" in res_payload["external_id"] else "aws",
                            "category": rule.category,
                            "rule_name": rule.name,
                            "severity": result.severity,
                            "priority": priority,
                            "current_state": result.current_state,
                            "recommended_state": result.recommended_state,
                            "estimated_savings": result.estimated_savings,
                            "confidence_score": confidence,
                            "business_impact": result.business_impact,
                            "technical_impact": result.technical_impact,
                            "risk_level": result.risk_level,
                            "rollback_complexity": result.rollback_complexity,
                            "status": "ACTIVE"
                        }

                        await recommendation_repository.create(db, obj_in=rec_data)
                        recommendation_count += 1
                        total_savings += result.estimated_savings
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.name} on resource {res.id}: {str(e)}")

        await db.flush()

        # Invalidate Redis caches
        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                cache_key = f"cloudpilot:proj:{project_id}:optimization:*"
                keys = await r.keys(cache_key)
                if keys:
                    await r.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to evict optimization cache: {str(e)}")

        return {
            "recommendations_count": recommendation_count,
            "total_savings": total_savings,
            "scan_timestamp": datetime.now(timezone.utc)
        }

    @staticmethod
    async def get_savings_summary(db: AsyncSession, project_id: uuid.UUID) -> dict:
        """Aggregates active potential savings (Redis cache-aside pattern)."""
        cache_key = f"cloudpilot:proj:{project_id}:optimization:savings"
        
        try:
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
            async with r:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache query failed: {str(e)}")

        recs = await recommendation_repository.get_by_project(db, project_id)
        
        total_monthly = sum(r.estimated_savings for r in recs)
        total_yearly = total_monthly * 12.0

        by_category = {}
        for r in recs:
            by_category[r.category] = by_category.get(r.category, 0.0) + r.estimated_savings

        response_data = {
            "total_savings_monthly": round(total_monthly, 2),
            "total_savings_yearly": round(total_yearly, 2),
            "by_category": by_category
        }

        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                await r.set(cache_key, json.dumps(response_data), ex=600)  # 10 minutes cache
        except Exception as e:
            logger.warning(f"Failed to cache savings summary: {str(e)}")

        return response_data
