# CloudPilot AI: Backend Foundation

This directory houses the Python-based backend service foundation for **CloudPilot AI**.

---

## 1. Local Development Instructions

### Prerequisites
* Python 3.12+
* Poetry (Python dependency manager) or pip
* Running instances of PostgreSQL and Redis

### Step 1: Clone and Configuration
1. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
2. Update `.env` variable values with your local parameters. Note that `DATABASE_URL` and `REDIS_URL` must point to your running database instances.

### Step 2: Dependency Installation
1. Install project dependencies using Poetry:
   ```bash
   poetry install
   ```
2. Or use pip:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Run Database Migrations
Run Alembic upgrades to generate database tables:
```bash
poetry run alembic upgrade head
```

### Step 4: Launching Server & Workers
* **FastAPI Server:**
  ```bash
  poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
  ```
* **Celery Worker:**
  ```bash
  poetry run celery -A app.workers.celery_app worker --loglevel=info
  ```

Once launched, you can inspect documentation at:
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 2. Running Automated Tests

Alembic migrations and endpoints are validated via Pytest:
```bash
poetry run pytest
```

---

## 3. Docker-Compose Setup

To spin up the entire foundation container ecosystem (Postgres, Redis, Backend, Workers) without installing local runtimes:

1. Build and launch services in detached mode:
   ```bash
   docker-compose up -d --build
   ```
2. Verify container health status:
   ```bash
   docker-compose ps
   ```
3. Run Alembic migrations inside the active backend container:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
4. Access endpoints on port `8000` (e.g. `http://localhost:8000/api/v1/health/health`).
5. Stop container stacks:
   ```bash
   docker-compose down -v
   ```

---

## 4. Connecting Cloud Accounts

Cloud integrations are linked via the `/api/v1/cloud/connect` endpoint. The credentials payload varies by provider.

### A. Amazon Web Services (AWS)
Provide an IAM Role Delegation ARN (recommended enterprise pattern):
```json
{
  "project_id": "YOUR_PROJECT_UUID",
  "provider_id": "aws",
  "name": "AWS Production Account",
  "account_identifier": "123456789012",
  "credentials": {
    "role_arn": "arn:aws:iam::123456789012:role/CloudPilotAccessRole",
    "external_id": "a9db58-c910-34ad-989d"
  },
  "settings": {
    "regions": ["us-east-1", "eu-west-1"]
  }
}
```

### B. Microsoft Azure
Provide Azure AD application registrations credentials:
```json
{
  "project_id": "YOUR_PROJECT_UUID",
  "provider_id": "azure",
  "name": "Azure Stage Subscription",
  "account_identifier": "azure-subscription-uuid",
  "credentials": {
    "tenant_id": "azure-tenant-uuid",
    "subscription_id": "azure-subscription-uuid",
    "client_id": "azure-client-uuid",
    "client_secret": "azure-client-secret-plaintext"
  },
  "settings": {}
}
```

### C. Google Cloud Platform (GCP)
Provide service account details in a JSON wrapper:
```json
{
  "project_id": "YOUR_PROJECT_UUID",
  "provider_id": "gcp",
  "name": "GCP Main Project",
  "account_identifier": "gcp-project-id",
  "credentials": {
    "service_account_json": {
      "type": "service_account",
      "project_id": "gcp-project-id",
      "private_key_id": "private-key-hash",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7...\n-----END PRIVATE KEY-----\n",
      "client_email": "cloudpilot-sync@gcp-project-id.iam.gserviceaccount.com"
    }
  },
  "settings": {}
}
```

---

## 5. Developer Guide: Adding a New Cloud Provider

To add support for a new cloud provider (e.g., **DigitalOcean**):

1. **Create the Adapter:**
   Create a new file `app/domains/cloud/adapters/digitalocean.py`. Subclass `CloudProviderAdapter` and implement all abstract methods:
   ```python
   from app.domains.cloud.adapters.base import CloudProviderAdapter, ConnectionConfig, NormalizedResourceDTO
   from app.domains.cloud.adapters.factory import ProviderAdapterFactory

   class DigitalOceanAdapter(CloudProviderAdapter):
       def connect(self, config: ConnectionConfig) -> None:
           # Initialize client library session...
           pass
       def validate_credentials(self) -> bool:
           # Run token verification check...
           return True
       def disconnect(self) -> None:
           pass
       def discover_resources(self) -> list[NormalizedResourceDTO]:
           # Discover droplets/volumes, normalize and return...
           return []
       # ... implement discover_regions, discover_services, etc.
   ```
2. **Register the Adapter:**
   At the end of your adapter file, register it with the factory registry:
   ```python
   ProviderAdapterFactory.register_adapter("digitalocean", DigitalOceanAdapter)
   ```
3. **Import the Module:**
   Import your adapter in `app/services/cloud.py` or within an initialization hook (e.g. `app/main.py`) to ensure the module loads and triggers the registration:
   ```python
   import app.domains.cloud.adapters.digitalocean
   ```
4. **Update Supported Providers List:**
   Extend the dictionary list returned inside the `get_cloud_providers()` endpoint under `app/api/v1/cloud.py` to display the option in the UI dashboard.

---

## 6. Connecting Monitoring Providers

Telemetry connections are linked via the `/api/v1/monitoring/connect` endpoint.

### A. Prometheus
```json
{
  "project_id": "YOUR_PROJECT_UUID",
  "provider_id": "prometheus",
  "name": "Prometheus Production K8s",
  "endpoint_url": "http://prometheus-k8s.monitoring.svc.cluster.local:9090",
  "credentials": {}
}
```

### B. Datadog
```json
{
  "project_id": "YOUR_PROJECT_UUID",
  "provider_id": "datadog",
  "name": "Datadog Workspace US",
  "endpoint_url": "https://api.datadoghq.com",
  "credentials": {
    "api_key": "YOUR_DATADOG_API_KEY",
    "application_key": "YOUR_DATADOG_APP_KEY"
  }
}
```

---

## 7. Developer Guide: Adding a New Monitoring Provider

To integrate a new monitoring platform (e.g. **Grafana Cloud** or **Dynatrace**):

1. **Create the Adapter:**
   Create a new file `app/domains/monitoring/adapters/dynatrace.py`. Subclass `MonitoringAdapter` and implement all abstract methods:
   ```python
   from datetime import datetime
   from app.domains.monitoring.adapters.base import MonitoringAdapter, MetricDataPoint
   from app.domains.monitoring.adapters.factory import MonitoringProviderFactory

   class DynatraceAdapter(MonitoringAdapter):
       def connect(self, endpoint_url: str, credentials: dict) -> None:
           # Initialize Client Connection...
           pass
       def validate(self) -> bool:
           # Check connection token scope validity...
           return True
       def disconnect(self) -> None:
           pass
       def fetch_time_series(self, query: str, start: datetime, end: datetime, step: int) -> list[MetricDataPoint]:
           # Make HTTP requests, parse json elements, return Normalized metrics DTOs...
           return []
       # ... implement other specific fetch_resource_metrics, fetch_pod_metrics etc.
   ```
2. **Register the Adapter:**
   At the end of your adapter file, register it with the factory registry:
   ```python
   # Register dynatrace in factory
   MonitoringProviderFactory.register_adapter("dynatrace", DynatraceAdapter)
   ```
3. **Import the Module:**
   Add an import statement in `app/domains/monitoring/adapters/__init__.py` to ensure the module registers when the app boots:
   ```python
   from app.domains.monitoring.adapters.dynatrace import DynatraceAdapter
   ```
4. **Update Supported Providers list:**
   Extend the static list returned in the `/monitoring/providers` endpoint under `app/api/v1/monitoring.py` to make the Dynatrace integration option visible to users.

---

## 8. Billing Synchronization Architecture

The Billing Engine aggregates multicloud spend records asynchronously utilizing the following model:

```mermaid
sequenceDiagram
    participant CB as Celery Beat
    participant CW as Celery Worker
    participant DB as PostgreSQL DB
    participant F as BillingProviderFactory
    participant P as Cloud Cost API
    
    CB->>CW: Dispatch jobs.billing.sync_accounts (Daily)
    CW->>DB: Query connected accounts (status = CONNECTED)
    DB-->>CW: Return Account List
    loop For each account
        CW->>F: Resolve BillingProvider
        F-->>CW: Return concrete adapter (AWS CE, Azure Query)
        CW->>P: Fetch daily cost range records
        P-->>CW: Return raw cost logs
        CW->>CW: Normalize into BillingRecordDTO
        CW->>DB: Bulk upsert billing records (map to resource UUID)
    end
```

---

## 9. Developer Guide: Adding a New Billing/Pricing Provider

To support a new cloud billing system (e.g., **Oracle Cloud Infrastructure (OCI)**):

1. **Create the Adapters:**
   Create a new file `app/domains/billing/adapters/oci.py`. Subclass `BillingProvider` and `PricingProvider` respectively:
   ```python
   from app.domains.billing.adapters.base import BillingProvider, PricingProvider, BillingRecordDTO, PricingRecordDTO
   from app.domains.billing.adapters.factory import BillingProviderFactory, PricingProviderFactory

   class OCIBillingProvider(BillingProvider):
       def connect(self, credentials: dict) -> None:
           # Init connection...
           pass
       def validate(self) -> bool:
           return True
       def fetch_historical_cost(self, start, end) -> list[BillingRecordDTO]:
           # Pull OCI usage reports...
           return []
       # ... implement other interface methods

   class OCIPricingProvider(PricingProvider):
       def fetch_compute_pricing(self, region: str) -> list[PricingRecordDTO]:
           # Query OCI public pricing API catalog...
           return []
       # ... implement other interface methods
   ```
2. **Register the Adapters:**
   Register your new classes at the end of the file:
   ```python
   BillingProviderFactory.register_adapter("oci", OCIBillingProvider)
   PricingProviderFactory.register_adapter("oci", OCIPricingProvider)
   ```
3. **Import the Module:**
   Import your adapter file in `app/domains/billing/adapters/__init__.py` to ensure it is registered on application load:
   ```python
   from app.domains.billing.adapters.oci import OCIBillingProvider, OCIPricingProvider
   ```
4. **Update Support list:**
   Update display parameters in the `/billing/dashboard` or similar endpoints to verify that OCI aggregations are active.

---

## 10. Optimization Engine Architecture

The Optimization Engine acts as a modular, deterministic rule evaluation layer, processing inventory catalog records and utilization metrics:

```mermaid
graph TD
    res[Active Resources] --> engine[Rule Engine Scanner]
    met[Telemetry Metrics] --> engine
    bill[Billing Records] --> engine
    engine --> rules[Registered Rule Checkers]
    rules --> eval[Evaluation Logic]
    eval --> score[Confidence & Priority Scoring]
    score --> db[PostgreSQL Recommendations]
```

---

## 11. Rule Engine & Extension Guide

To add a custom optimization rule (e.g. **Idle Database Replicas**):

1. **Create the Rule Class:**
   Create a new file `app/domains/optimization/rules/replicas.py`. Subclass `OptimizationRule` and implement all abstract properties and methods:
   ```python
   from app.domains.optimization.rules.base import OptimizationRule, RuleEvaluationContext, RuleEvaluationResult
   from app.domains.optimization.rules.registry import RuleRegistry

   class IdleReplicaRule(OptimizationRule):
       @property
       def name(self) -> str:
           return "idle_database_replica"
       @property
       def category(self) -> str:
           return "database"
       @property
       def applicable_providers(self) -> list[str]:
           return ["aws", "gcp"]
       @property
       def applicable_resource_types(self) -> list[str]:
           return ["database_replica", "database"]
           
       def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
           # Execute deterministic checks...
           # If replica has 0 connections, recommend deletion:
           return RuleEvaluationResult(
               is_applicable=True,
               current_state={"connections": 0},
               recommended_state={"action": "Delete replica"},
               estimated_savings=25.0,
               severity="medium",
               risk_level="low"
           )
   ```
2. **Register the Rule:**
   At the end of your rule file, register it with the rule registry:
   ```python
   RuleRegistry.register_rule(IdleReplicaRule())
   ```
3. **Import the Module:**
   Import your module in `app/domains/optimization/rules/__init__.py` to trigger the registration:
   ```python
   import app.domains.optimization.rules.replicas
   ```

---

## 12. Savings & Confidence Models

### A. Savings Calculation
Savings estimates are calculated based on hourly rate differences:
* **Idle instances:** Stopped recommendations calculate $S = R_h \times 730$ (full monthly hourly rate).
* **Rightsizing compute:** Downsizing recommendations calculate $S = (R_{\text{current}} - R_{\text{target}}) \times 730$.
* **Unattached Storage:** Disk deletion recommendations calculate $S = G \times 0.10$ (gigabyte capacity multiplied by standard monthly EBS rate).

### B. Confidence Scoring (0-100)
Confidence levels are computed using historical telemetry stability:
* **Base score:** Starts at 80.
* **Telemetry history:** Deduct 20 points if fewer than 5 metric samples exist.
* **Metric stability:** Deduct 15 points if the standard deviation of CPU utilization is high (> 15% variance).
* **Resource age:** Deduct 10 points if the resource is less than 3 days old.

### C. Priority Ranking
Priority is resolved using a deterministic matrix combining savings, risk level, and severity:
* **High Priority:** Severity is `critical` (security risk), or monthly savings > $100 with `low` implementation risk.
* **Medium Priority:** Savings > $20 with `low` or `medium` risk.
* **Low Priority:** Default for low savings or high-risk changes.

---

## 13. AI Copilot Agent Architecture

The AI DevOps Copilot uses a decoupled tool-calling loop. It interacts with cloud provider data solely through internal, normalized service layers:

```mermaid
sequenceDiagram
    participant User as Chat API Client
    participant AI as AIService
    participant LLM as LLMProvider (OpenAI, Claude)
    participant TR as AIToolRegistry
    participant Tool as AITool (Resource, Billing)
    
    User->>AI: Submit message query ("Why is my bill high?")
    AI->>LLM: Request completion (Include tool schemas)
    LLM-->>AI: Return tool calling request (e.g. get_billing_summary)
    AI->>TR: Resolve Tool by name
    TR->>Tool: Execute tool (Query DB via service layer)
    Tool-->>AI: Return normalized JSON cost data
    AI->>LLM: Resubmit conversation context + Tool outcome
    LLM-->>AI: Return final assistant explanation text
    AI-->>User: Return response Message
```

---

## 14. Developer Guide: Extending the AI Layer

### A. Adding a New LLM Provider (e.g., Cohere)
1. **Create the Provider Adapter:**
   Create `app/domains/ai/providers/cohere.py` subclassing `LLMProvider`:
   ```python
   from app.domains.ai.providers.base import LLMProvider, LLMMessage, LLMResponse
   from app.domains.ai.providers.factory import LLMProviderFactory

   class CohereProvider(LLMProvider):
       def connect(self, api_key: str, model_name: str, settings: dict) -> None:
           # Init Cohere client...
           pass
       def chat(self, messages, system_prompt, tools=None) -> LLMResponse:
           # Execute chat completions...
           return LLMResponse(content="Cohere text response")
       # ... implement other interface methods (stream_chat, health_check)
   ```
2. **Register the Provider:**
   ```python
   LLMProviderFactory.register_provider("cohere", CohereProvider)
   ```
3. **Import the Module:**
   Import cohere in `app/domains/ai/providers/__init__.py`.

### B. Adding a New AI Agent Tool (e.g., Security Advisor)
1. **Create the Tool:**
   Create a new file `app/domains/ai/tools/security.py` subclassing `AITool`:
   ```python
   from app.domains.ai.tools.base import AITool, AIToolRegistry

   class SecurityAdvisorTool(AITool):
       @property
       def name(self) -> str:
           return "get_security_findings"
       @property
       def description(self) -> str:
           return "Retrieves active security recommendations and public exposure vulnerabilities."
       @property
       def parameters(self) -> dict:
           return {"type": "object", "properties": {}}
           
       async def execute(self, db, project_id, arguments) -> dict:
           # Query normalized recommendations service...
           return {"findings": []}
   ```
2. **Register the Tool:**
   At the end of your file:
   ```python
   AIToolRegistry.register_tool(SecurityAdvisorTool())
   ```
3. **Import the Module:**
   Import your file in `app/domains/ai/tools/__init__.py`.





