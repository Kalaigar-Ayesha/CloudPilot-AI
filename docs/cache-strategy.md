# Redis Caching Strategy

This document details the Redis caching design, key conventions, time-to-live (TTL) limits, and cache invalidation policies for **CloudPilot AI**.

---

## 1. Caching Model & Serialization

* **Caching Pattern:** **Cache-Aside (Lazy Loading)**. Application services query Redis first. On cache miss, they fetch from PostgreSQL, write to Redis, and return the result.
* **Serialization Format:** **MessagePack** (binary serialization) for high-performance time-series metrics and resources. **JSON** is used for structured objects (like configuration values) to simplify debugging.

---

## 2. Caching Scopes, Keys & TTL Guidelines

To maintain namespace sanity, keys are prefixed using `cloudpilot:`.

| Data Domain | Redis Key Template | TTL | Rationale / Notes |
| :--- | :--- | :--- | :--- |
| **Billing Summaries** | `cloudpilot:proj:{proj_uuid}:bill:sum:{start_date}:{end_date}` | **1 Hour** | Cost data is computed periodically. 1 hour cache is safe since values only change on next collector run. |
| **Resource Inventory**| `cloudpilot:proj:{proj_uuid}:res:list:{filter_hash}` | **30 Min** | Discovered resources are updated in batches. Avoids querying database joins frequently. |
| **Resource Metrics** | `cloudpilot:res:{res_uuid}:metrics:{metric_type}:{window_hash}`| **5 Min** | Performance time-series data changes frequently. Short TTL prevents querying large Postgres datasets. |
| **Pricing Catalog** | `cloudpilot:provider:{provider_id}:sku:{sku_id}` | **24 Hours**| Public instance pricing changes rarely. Extremely long cache prevents redundant table queries. |
| **Recommendations** | `cloudpilot:proj:{proj_uuid}:recs:list` | **1 Hour** | Recommendations are computed daily. Avoids recurring calculations. |
| **Forecast Reports** | `cloudpilot:proj:{proj_uuid}:forecast:{month_count}` | **12 Hours**| Forecast models run every 12 hours. |
| **Rate Limit Counters**| `cloudpilot:rate:{user_uuid or ip}:window` | **1 Min** | Tracks Token Bucket values for rate limits. |

---

## 3. Cache Invalidation Triggers

Caching relies on explicit invalidation events triggered by Celery jobs rather than relying solely on TTL expiration:

```
                  Celery Worker resource_sync_task()
                                │
                                ▼
                   Upsert database records
                                │
                                ▼
               Publish invalidation event to Redis
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
        Evict resource cache       Evict billing summaries cache
    (DEL cloudpilot:proj:res:*)    (DEL cloudpilot:proj:bill:*)
```

1. **Inventory Updates:** When `resource_sync_task` completes, it issues a command to scan and delete keys matching `cloudpilot:proj:{proj_uuid}:res:list:*`.
2. **Billing Ingestion:** When new billing reports are saved, it deletes keys matching `cloudpilot:proj:{proj_uuid}:bill:*`.
3. **Recommendation Computations:** When `run_optimization_rules` completes, it deletes `cloudpilot:proj:{proj_uuid}:recs:list`.
