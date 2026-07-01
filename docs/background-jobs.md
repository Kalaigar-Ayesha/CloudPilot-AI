# Background & Scheduled Jobs Architecture

This document details the background task and scheduling architecture using **Celery** and **Celery Beat** for **CloudPilot AI**.

---

## 1. Celery Worker Queue Topologies

To prevent long-running tasks (like loading billing reports) from blocking quick tasks (like sending a notification or caching a query), workers are assigned to distinct queues:

* **`discovery`**: Performs API operations for cloud resource detection.
* **`billing`**: Processes large billing CSVs and aggregates transaction records.
* **`metrics`**: Polls telemetry metrics from monitoring provider endpoints.
* **`optimization`**: Runs the rules engine calculations.
* **`default`**: Handles short jobs like email dispatches, audit logging, and cache invalidation alerts.

---

## 2. Job Schedule Registry

These tasks are orchestrated by Celery Beat:

| Job Name | Celery Task Name | Schedule | Target Queue | Parameter Inputs |
| :--- | :--- | :--- | :--- | :--- |
| **Sync Resources** | `jobs.discovery.sync_all_accounts` | **Every 6 Hours** | `discovery` | None (Iterates active database accounts) |
| **Sync Billing** | `jobs.billing.sync_billing_manifests` | **Daily at 01:00 UTC** | `billing` | `date_range` (default: yesterday) |
| **Sync Metrics** | `jobs.metrics.sync_resource_metrics` | **Every 15 Minutes**| `metrics` | `window_minutes` (default: 15) |
| **Refresh Pricing** | `jobs.billing.refresh_public_pricing` | **Weekly (Sun 00:00 UTC)** | `billing` | `provider_list` |
| **Run Optimization** | `jobs.optimization.evaluate_rules` | **Daily at 03:00 UTC** | `optimization` | None (Runs for all accounts) |
| **Generate Forecast**| `jobs.optimization.run_forecast_models`| **Daily at 04:00 UTC** | `optimization` | None (Runs for all projects) |
| **Cleanup Logs** | `jobs.operations.purge_expired_logs` | **Weekly (Sun 02:00 UTC)** | `default` | `retention_days` (default: 90) |
| **Send Notifications**| `jobs.notifications.dispatch_queue` | **Immediate (Event)** | `default` | `notification_payload` |

---

## 3. Job Implementation Details

### 3.1 Sync Resources (`jobs.discovery.sync_all_accounts`)
1. **Fetch Inventory:** Queries `cloud_accounts` database rows where status is `CONNECTED`.
2. **Batch Dispatch:** Dispatches parallel `sync_single_account(account_id)` tasks to the `discovery` queue.
3. **Scan Execution:** Instantiates the cloud adapter (`CloudProviderAdapter`), retrieves resources, compares them with database state, writes changes, and flags removed items.

### 3.2 Sync Billing (`jobs.billing.sync_billing_manifests`)
1. **Target Ingestion:** Queries billing manifest paths configured per account.
2. **Download Stream:** Downloads CSV or Parquet files from S3/Azure Blob Storage.
3. **Parse & Normalize:** Ingests rows in 10,000-record chunks using pandas to prevent process memory exhaustion.
4. **Data Save:** Writes normalized records to `billing_records` and invalidates billing caches.

### 3.3 Sync Metrics (`jobs.metrics.sync_resource_metrics`)
1. **Target Gathering:** Queries resources of type `VIRTUAL_MACHINE` and `DATABASE` that are currently `running`.
2. **Adapter Mapping:** Connects to the workspace's monitoring adapter (`MonitoringAdapter`).
3. **Poll Run:** Fetches standard variables (CPU, memory, IOPS) for the query window.
4. **Write-out:** Inserts metric records into `resource_metrics` partition tables.

### 3.4 Run Optimization (`jobs.optimization.evaluate_rules`)
1. **Context Load:** Queries resource tables, billing data, and metric histories.
2. **Strategy Run:** Evaluates the registered rules (`OptimizationRule`) against target inventories.
3. **Recommendation Processing:** Saves recommendations to `optimization_recommendations`, updates statuses, and triggers notifications if new recommendations are generated.

---

## 4. Resilience & Retry Strategy

To handle API rate limits and network timeouts:

* **Exponential Backoff:** Retried tasks calculate delays using:
  $$\text{delay} = \text{default\_retry\_delay} \times 2^{\text{retries}} + \text{random\_jitter}$$
  * `default_retry_delay` = 60 seconds.
  * `max_retries` = 5.
* **Idempotency:** All tasks are designed to be idempotent. If a sync job runs twice, it will update existing records without writing duplicate data.
* **Dead Letter Queue (DLQ):** Tasks that fail all 5 retry attempts are written to `scheduled_jobs` with a `FAILED` status, logging the stack trace for administrator review.
