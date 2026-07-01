# CloudPilot AI: Architecture & System Design Handbook

This guide contains complete diagrams detailing request flows, class layouts, entity relationships, and deployment architectures.

---

## 1. System Request Flow Diagram

This flow diagram illustrates how user requests route through the system:

```mermaid
graph TD
    User([User Client]) -->|HTTPS / WSS| Ingress[Kubernetes Ingress]
    Ingress -->|Route api/*| API[FastAPI Server]
    Ingress -->|Route /*| UI[React Frontend]
    API -->|Async Task| Redis[(Redis Broker)]
    Redis -->|Process Scan| Worker[Celery Background Workers]
    API -->|ORM Query| DB[(PostgreSQL Database)]
    Worker -->|Fetch Metrics| Telemetry[Prometheus / CloudWatch / Datadog]
    Worker -->|Save Discoveries| DB
```

---

## 2. Entity Relationship Diagram (ERD)

This entity relationship diagram maps the database schemas and relationships:

```mermaid
erDiagram
    CL_ACCOUNT ||--o{ CL_RESOURCE : discovers
    CL_RESOURCE ||--o{ RC_METRIC : registers
    CL_RESOURCE ||--o{ REC_OPTIMIZATION : generates
    CL_ACCOUNT ||--o{ BILL_RECORD : logs
    
    CL_ACCOUNT {
        uuid id PK
        uuid project_id
        string name
        string provider_id
        string status
    }
    CL_RESOURCE {
        uuid id PK
        uuid account_id FK
        string name
        string resource_type
        string status
    }
    RC_METRIC {
        uuid id PK
        uuid resource_id FK
        float cpu_utilization
        float memory_utilization
        datetime timestamp
    }
    REC_OPTIMIZATION {
        uuid id PK
        uuid resource_id FK
        string rule_name
        string severity
        float estimated_savings
        integer confidence_score
    }
    BILL_RECORD {
        uuid id PK
        uuid account_id FK
        float cost
        string category
        datetime billing_period
    }
```

---

## 3. Core AI Chat Sequence Diagram

This sequence diagram details how the AI DevOps Copilot executes agent loops:

```mermaid
sequenceDiagram
    participant UI as React UI (Copilot)
    participant API as AIService (FastAPI)
    participant LLM as LLMProvider (OpenAI)
    participant Tool as AITool (Resource, Billing)

    UI->>API: POST /query ("What is my AWS spend?")
    API->>LLM: Chat completion request (messages + tools schema)
    LLM-->>API: Returns Tool Call request (get_billing_summary)
    API->>Tool: Execute (fetch billing metrics)
    Tool-->>API: Returns JSON Billing data
    API->>LLM: Resubmit context + tool outcome
    LLM-->>API: Returns final response text
    API->>UI: Response Message (with collapsible citations)
```

---

## 4. Kubernetes Deployment Diagram

This deployment diagram maps the target high-availability Kubernetes infrastructure layout:

```mermaid
graph TB
    subgraph VPC [Cloud Network VPC]
        Ingress[Ingress Controller LoadBalancer]
        subgraph Nodes [EKS / AKS / GKE Node Groups]
            UI_Pod1[React UI Pod 1]
            UI_Pod2[React UI Pod 2]
            API_Pod1[FastAPI Pod 1]
            API_Pod2[FastAPI Pod 2]
            Worker_Pod[Celery Worker Pod]
        end
        subgraph State [State Layer]
            DB[(RDS Postgres Database)]
            Cache[(ElastiCache Redis)]
        end
    end
    Ingress --> UI_Pod1
    Ingress --> UI_Pod2
    Ingress --> API_Pod1
    Ingress --> API_Pod2
    API_Pod1 --> Cache
    Worker_Pod --> Cache
    API_Pod1 --> DB
    Worker_Pod --> DB
```
